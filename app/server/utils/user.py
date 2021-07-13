import threading
from functools import cmp_to_key
from typing import Optional, List
from phonenumbers.phonenumberutil import NumberParseException
from sqlalchemy.orm.attributes import flag_modified
from bit import base58
from flask import current_app, g
from eth_utils import to_checksum_address
import sentry_sdk
import config

from server import db
from server.models.device_info import DeviceInfo
from server.models.organisation import Organisation
from server.models.token import Token
from server.models.transfer_usage import TransferUsage
from server.models.upload import UploadedResource
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.custom_attribute import CustomAttribute
from server.models.transfer_card import TransferCard
from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.blockchain_address import BlockchainAddress
from server.schemas import user_schema
from server.constants import DEFAULT_ATTRIBUTES, KOBO_META_ATTRIBUTES, ASSIGNABLE_TIERS
from server.exceptions import PhoneVerificationError, TransferAccountNotFoundError
from server import celery_app
from server.utils.phone import send_message
from server.utils.phone import proccess_phone_number
from server.utils.amazon_s3 import generate_new_filename, save_to_s3_from_url, LoadFileException
from server.utils.internationalization import i18n_for
from server.utils.misc import rounded_dollars
from server.utils.multi_chain import get_chain

def save_photo_and_check_for_duplicate(url, new_filename, image_id):
    save_to_s3_from_url(url, new_filename)

    try:
        rekognition_task = celery_app.signature('worker.celery_tasks.check_for_duplicate_person',
                                                args=(new_filename, image_id))
        # TODO: Standardize this task (pipe through execute_synchronous_celery)
        rekognition_task.delay()
    except Exception as e:
        print(e)
        sentry_sdk.capture_exception(e)
        pass


def find_oldest_user_for_transfer_account(transfer_account):
    oldest_user = None
    for user in transfer_account.user:
        if oldest_user:
            if user.created < oldest_user.created:
                oldest_user = user
        else:
            oldest_user = user

    return oldest_user


def find_user_from_public_identifier(*public_identifiers):
    """
    :param public_identifiers: email, phone, public_serial_number, nfc_serial_number or address
    :return: First user found
    """
    user = None
    transfer_card = None

    for public_identifier in list(filter(lambda x: x is not None, public_identifiers)):
        if public_identifier is None:
            continue

        user = User.query.execution_options(show_all=True).filter_by(
            email=str(public_identifier).lower()).first()
        if user:
            break

        try:
            user = User.query.execution_options(show_all=True).filter_by(
                phone=proccess_phone_number(public_identifier)).first()
            if user:
                break
        except NumberParseException:
            pass

        transfer_card = TransferCard.query.execution_options(show_all=True).filter_by(
            public_serial_number=str(public_identifier).lower()).first()
        user = transfer_card and transfer_card.user

        if user:
            break

        transfer_card = TransferCard.query.execution_options(show_all=True).filter_by(
            nfc_serial_number=public_identifier.upper()).first()
        user = transfer_card and transfer_card.user

        if user:
            break

        user = User.query.execution_options(show_all=True).filter_by(
            uuid=public_identifier).first()
        if user:
            break

        try:
            checksummed = to_checksum_address(public_identifier)
            blockchain_address = BlockchainAddress.query.filter_by(
                address=checksummed).first()

            if blockchain_address and blockchain_address.transfer_account:
                user = blockchain_address.transfer_account.primary_user
                if user:
                    break

        except Exception:
            pass

    return user, transfer_card


def update_transfer_account_user(user,
                                 first_name=None, last_name=None, preferred_language=None,
                                 phone=None, email=None, public_serial_number=None,
                                 use_precreated_pin=False,
                                 existing_transfer_account=None,
                                 roles=None,
                                 default_organisation_id=None,
                                 business_usage=None):
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if preferred_language:
        user.preferred_language = preferred_language
    if phone:
        user.phone = phone
    if email:
        user.email = email
    if public_serial_number:
        user.public_serial_number = public_serial_number
        transfer_card = TransferCard.get_transfer_card(public_serial_number)
        user.default_transfer_account.transfer_card = transfer_card
        if transfer_card:
            transfer_card.update_transfer_card()
    else:
        transfer_card = None

    if default_organisation_id:
        user.default_organisation_id = default_organisation_id

    if use_precreated_pin and transfer_card:
        user.set_pin(transfer_card.PIN)

    if existing_transfer_account:
        user.transfer_accounts.append(existing_transfer_account)

    if business_usage:
        user.business_usage_id = business_usage.id

    # remove all roles before updating
    user.remove_all_held_roles()
    flag_modified(user, '_held_roles')

    if roles:
        for role in roles:
            user.set_held_role(role[0], role[1])

    return user


def create_transfer_account_user(first_name=None, last_name=None, preferred_language=None,
                                 phone=None, email=None, public_serial_number=None, uuid=None,
                                 organisation: Organisation=None,
                                 token=None,
                                 blockchain_address=None,
                                 transfer_account_name=None,
                                 use_precreated_pin=False,
                                 use_last_4_digits_of_id_as_initial_pin=False,
                                 existing_transfer_account=None,
                                 roles=None,
                                 is_self_sign_up=False,
                                 business_usage=None,
                                 initial_disbursement=None):

    user = User(first_name=first_name,
                last_name=last_name,
                preferred_language=preferred_language,
                blockchain_address=blockchain_address,
                phone=phone,
                email=email,
                uuid=uuid,
                public_serial_number=public_serial_number,
                is_self_sign_up=is_self_sign_up,
                business_usage=business_usage)

    precreated_pin = None
    is_activated = False

    try:
        transfer_card = TransferCard.get_transfer_card(public_serial_number)
    except Exception as e:
        transfer_card = None

    if use_precreated_pin:
        precreated_pin = transfer_card.PIN
        is_activated = True

    elif use_last_4_digits_of_id_as_initial_pin:
        precreated_pin = str(public_serial_number or phone)[-4:]
        is_activated = False

    user.set_pin(precreated_pin, is_activated)

    if roles:
        for role in roles:
            user.set_held_role(role[0], role[1])
    else:
        user.remove_all_held_roles()

    if not organisation:
        organisation = Organisation.master_organisation()

    user.add_user_to_organisation(organisation, is_admin=False)

    db.session.add(user)

    if existing_transfer_account:
        transfer_account = existing_transfer_account
        user.transfer_accounts.append(existing_transfer_account)
    else:
        transfer_account = TransferAccount(
            bound_entity=user,
            blockchain_address=blockchain_address,
            organisation=organisation
        )

        top_level_roles = [r[0] for r in roles or []]
        is_vendor = 'VENDOR' in top_level_roles
        is_beneficiary = 'BENEFICIARY' in top_level_roles

        transfer_account.name = transfer_account_name
        transfer_account.is_vendor = is_vendor
        transfer_account.is_beneficiary = is_beneficiary

        if transfer_card:
            transfer_account.transfer_card = transfer_card

        if token:
            transfer_account.token = token

        if not is_self_sign_up:
            transfer_account.approve_and_disburse(initial_disbursement=initial_disbursement)

        db.session.add(transfer_account)

    user.default_transfer_account = transfer_account

    return user

def save_device_info(device_info, user):
    add_device = False

    if device_info['uniqueId'] and not DeviceInfo.query.filter_by(
            unique_id=device_info['uniqueId']).first():
        # Add the device if the uniqueId is defined, and isn't already in db
        add_device = True

    if add_device:
        device = DeviceInfo()

        device.unique_id = device_info['uniqueId']
        device.brand = device_info['brand']
        device.model = device_info['model']
        device.width = device_info['width']
        device.height = device_info['height']

        device.user = user

        db.session.add(device)

        return device


def set_custom_attributes(attribute_dict, user):
    # loads in any existing custom attributes
    custom_attributes = user.custom_attributes or []
    for key in attribute_dict['custom_attributes'].keys():
        custom_attribute = CustomAttribute.query.filter(CustomAttribute.name == key).first()
        if not custom_attribute:
            custom_attribute = CustomAttribute()
            custom_attribute.name = key
            db.session.add(custom_attribute)

        # Put validation logic here!
        value = attribute_dict['custom_attributes'][key]
        value = custom_attribute.clean_and_validate_custom_attribute(value)
        
        to_remove = list(filter(lambda a: a.custom_attribute.name == key, custom_attributes))
        for r in to_remove:
            custom_attributes.remove(r)
            db.session.delete(r)

        custom_attribute = CustomAttributeUserStorage(
            custom_attribute=custom_attribute, value=value)

        custom_attributes.append(custom_attribute)
    custom_attributes = set_attachments(
        attribute_dict, user, custom_attributes)
    user.custom_attributes = custom_attributes
    return custom_attributes


def set_attachments(attribute_dict, user, custom_attributes):
    attachments = attribute_dict.get('_attachments', [])

    for attachment in attachments:
        submitted_filename = attachment['filename'].split('/')[-1]
        for attribute in custom_attributes:
            if submitted_filename == attribute.value:
                type = 'custom_attribute_{}'.format(attribute)

                new_filename = generate_new_filename(
                    submitted_filename, type, 'KOBO')

                uploaded_image = UploadedResource(filename=new_filename, file_type=type)

                uploaded_image.user = user

                db.session.add(uploaded_image)

                db.session.flush()

                try:

                    if attribute == 'profile_picture':

                        t = threading.Thread(target=save_photo_and_check_for_duplicate,
                                             args=(attachment['download_url'], new_filename, uploaded_image.id))
                    else:
                        t = threading.Thread(target=save_to_s3_from_url,
                                             args=(attachment['download_url'], new_filename))

                    t.daemon = True
                    t.start()

                except LoadFileException:
                    print("File has likely expired")
                    pass

                attribute.value = new_filename
                attribute.uploaded_image_id = uploaded_image.id
                continue

    return custom_attributes


def set_location_conditionally(user, location, gps_location = None):

    if gps_location:
        try:
            gps = gps_location.split(' ')
            lat = float(gps[0])
            lng = float(gps[1])
        except (SyntaxError, IndexError, ValueError):
            lat = None
            lng = None

    else:
        lat = None
        lng = None

    # Set the location, only updating the latlng if it hasn't been explicitly provided
    if lat and lng:
        user.lat = lat
        user.lng = lng
        if location:
            user.location = location

    else:
        if location:
            user.location = location
            user.attempt_update_gps_location()


def send_one_time_code(phone, user):
    try:
        send_phone_verification_message(
            to_phone=phone, one_time_code=user.one_time_code)

    except Exception as e:
        raise PhoneVerificationError(
            'Something went wrong. ERROR: {}'.format(e))


def proccess_create_or_modify_user_request(
        attribute_dict,
        organisation=None,
        allow_existing_user_modify=False,
        is_self_sign_up=False,
        modify_only=False
):
    """
    Takes a create or modify user request and determines the response. Normally what's in the top level API function,
    but here it's one layer down because there's multiple entry points for 'create user':
    - The admin api
    - The register api

    :param attribute_dict: attributes that can be supplied by the request maker
    :param organisation:  what organisation the request maker belongs to. The created user is bound to the same org
    :param allow_existing_user_modify: whether to return an error when the user already exists for the supplied IDs
    :param is_self_sign_up: does the request come from the register api?
    :param modify_only: whether to allow the creation of a  new user
    :return: An http response
    """
    if not attribute_dict.get('custom_attributes'):
        attribute_dict['custom_attributes'] = {}

    user_id = attribute_dict.get('user_id')

    email = attribute_dict.get('email')
    phone = attribute_dict.get('phone')

    account_types = attribute_dict.get('account_types', [])
    if isinstance(account_types, str):
        account_types = account_types.split(',')

    referred_by = attribute_dict.get('referred_by')

    blockchain_address = attribute_dict.get('blockchain_address')

    provided_public_serial_number = attribute_dict.get('public_serial_number')

    uuid = attribute_dict.get('uuid')

    require_identifier = attribute_dict.get('require_identifier', True)

    if not user_id:
        # Extract ID from Combined User ID and Name String if it exists
        try:
            user_id_name_string = attribute_dict.get('user_id_name_string')

            user_id_str = user_id_name_string and user_id_name_string.split(':')[0]

            if user_id_str:
                user_id = int(user_id_str)

        except SyntaxError:
            pass

    if not blockchain_address and provided_public_serial_number:

        try:
            blockchain_address = to_checksum_address(
                provided_public_serial_number)

            # Since it's actually an ethereum address set the provided public serial number to None
            # so it doesn't get used as a transfer card
            provided_public_serial_number = None
        except Exception:
            pass

    require_transfer_card_exists = attribute_dict.get(
        'require_transfer_card_exists', g.active_organisation.require_transfer_card)

    public_serial_number = (provided_public_serial_number
                            or attribute_dict.get('payment_card_qr_code')
                            or attribute_dict.get('payment_card_barcode'))

    location = attribute_dict.get('location')  # address location

    # Yes, we know "GPS" refers to a technology, but "gps_location" is less ambiguous for end users than "geo_location"
    gps_location = attribute_dict.get('gps_location')  # geo location as str of lat, lng

    use_precreated_pin = attribute_dict.get('use_precreated_pin')
    use_last_4_digits_of_id_as_initial_pin = attribute_dict.get(
        'use_last_4_digits_of_id_as_initial_pin')

    transfer_account_name = attribute_dict.get('transfer_account_name')
    first_name = attribute_dict.get('first_name')
    last_name = attribute_dict.get('last_name')

    business_usage_name = attribute_dict.get('business_usage_name')
    business_usage_id = None
    if business_usage_name:
        usage = TransferUsage.find_or_create(business_usage_name)
        business_usage_id = usage.id

    preferred_language = attribute_dict.get('preferred_language')

    primary_user_identifier = attribute_dict.get('primary_user_identifier')
    primary_user_pin = attribute_dict.get('primary_user_pin')

    initial_disbursement = attribute_dict.get('initial_disbursement', None)
    if not account_types:
        account_types = ['beneficiary']
    roles_to_set = []
    for at in account_types:
        if at not in g.active_organisation.valid_roles:
            raise Exception(f'{at} not a valid role for this organisation. Please choose one of the following: {g.active_organisation.valid_roles}')
        roles_to_set.append((ASSIGNABLE_TIERS[at], at))

    chain = get_chain()
    if current_app.config['CHAINS'][chain]['IS_USING_BITCOIN']:
        try:
            base58.b58decode_check(blockchain_address)
        except ValueError:
            response_object = {
                'message': 'Blockchain Address {} Not Valid'.format(blockchain_address)}
            return response_object, 400

    if isinstance(phone, bool):
        phone = None

    if phone and not is_self_sign_up:
        # phone has already been parsed if self sign up
        try:
            phone = proccess_phone_number(phone)
        except NumberParseException as e:
            response_object = {'message': 'Invalid Phone Number: ' + str(e)}
            return response_object, 400

    # Work out if there's an existing transfer account to bind to
    existing_transfer_account = None
    if primary_user_identifier:
        primary_user, _ = find_user_from_public_identifier(
            primary_user_identifier)
        if not primary_user or not primary_user.verify_password(primary_user_pin):
            response_object = {'message': 'Primary User not Found'}
            return response_object, 400

        if not primary_user.verify_password(primary_user_pin):
            response_object = {'message': 'Invalid PIN for Primary User'}
            return response_object, 400

        primary_user_transfer_account = primary_user.transfer_account

        if not primary_user_transfer_account:
            response_object = {
                'message': 'Primary User has no transfer account'}
            return response_object, 400

    if not (phone or email or public_serial_number or blockchain_address or user_id or uuid or not require_identifier):
        response_object = {'message': 'Must provide a unique identifier'}
        return response_object, 400

    if use_precreated_pin and not public_serial_number:
        response_object = {
            'message': 'Must provide public serial number to use a transfer card or pre-created pin'
        }
        return response_object, 400

    if public_serial_number:
        public_serial_number = str(public_serial_number)

        if use_precreated_pin or require_transfer_card_exists:
            transfer_card = TransferCard.query.filter_by(
                public_serial_number=public_serial_number).first()

            if not transfer_card:
                response_object = {'message': 'Transfer card not found'}
                return response_object, 400

    business_usage = None
    if business_usage_id:
        business_usage = TransferUsage.query.get(business_usage_id)
        if not business_usage:
            response_object = {
                'message': f'Business Usage not found for id {business_usage_id}'
            }
            return response_object, 400

    referred_by_user, _ = find_user_from_public_identifier(referred_by)

    if referred_by and not referred_by_user:
        response_object = {
            'message': f'Referrer user not found for public identifier {referred_by}'
        }
        return response_object, 400

    existing_user, _ = find_user_from_public_identifier(
        email, phone, public_serial_number, blockchain_address, uuid)

    if not existing_user and user_id:
        existing_user = User.query.get(user_id)

    if modify_only and existing_user is None:
        response_object = {'message': 'User not found'}
        return response_object, 404

    if existing_user:
        if not allow_existing_user_modify:
            response_object = {'message': 'User already exists for Identifier'}
            return response_object, 400

        if user_id is not None and (existing_user.id != user_id) and existing_user.phone == phone:
            response_object = {'message': f'User already exists for phone {existing_user}'}
            return response_object, 400

        try:

            user = update_transfer_account_user(
                existing_user,
                first_name=first_name,
                last_name=last_name,
                preferred_language=preferred_language,
                phone=phone,
                email=email,
                public_serial_number=public_serial_number,
                use_precreated_pin=use_precreated_pin,
                existing_transfer_account=existing_transfer_account,
                roles=roles_to_set,
                business_usage=business_usage
            )

            set_location_conditionally(user, location, gps_location)

            if referred_by_user:
                user.referred_by.clear()  # otherwise prior referrals will remain...
                user.referred_by.append(referred_by_user)

            set_custom_attributes(attribute_dict, user)
            flag_modified(user, "custom_attributes")

            db.session.commit()

            response_object = {
                'message': 'User Updated',
                'data': {'user': user_schema.dump(user).data}
            }

            return response_object, 200

        except Exception as e:
            response_object = {
                'message': str(e)
            }

            return response_object, 400

    user = create_transfer_account_user(
        first_name=first_name, last_name=last_name, preferred_language=preferred_language,
        phone=phone, email=email, public_serial_number=public_serial_number, uuid=uuid,
        organisation=organisation if organisation else g.active_organisation,
        blockchain_address=blockchain_address,
        transfer_account_name=transfer_account_name,
        use_precreated_pin=use_precreated_pin,
        use_last_4_digits_of_id_as_initial_pin=use_last_4_digits_of_id_as_initial_pin,
        existing_transfer_account=existing_transfer_account,
        roles=roles_to_set,
        is_self_sign_up=is_self_sign_up,
        business_usage=business_usage, initial_disbursement=initial_disbursement)

    set_location_conditionally(user, location, gps_location)

    if referred_by_user:
        user.referred_by.append(referred_by_user)

    if attribute_dict.get('gender'):
        attribute_dict['custom_attributes']['gender'] = attribute_dict.get('gender')

    if attribute_dict.get('bio'):
        attribute_dict['custom_attributes']['bio'] = attribute_dict.get('bio')

    set_custom_attributes(attribute_dict, user)

    if is_self_sign_up and attribute_dict.get('deviceInfo', None) is not None:
        save_device_info(device_info=attribute_dict.get(
            'deviceInfo'), user=user)
    # Location fires an async task that needs to know user ID
    db.session.flush()

    if phone:
        if is_self_sign_up:
            send_one_time_code(phone=phone, user=user)
            return {'message': 'User Created. Please verify phone number.', 'otp_verify': True}, 200

        elif current_app.config['ONBOARDING_SMS']:
            try:
                send_onboarding_sms_messages(user)
            except Exception as e:
                print(e)
                sentry_sdk.capture_exception(e)
                pass

    response_object = {
        'message': 'User Created',
        'data': {
            'user': user_schema.dump(user).data
        }
    }

    return response_object, 200


def send_onboarding_sms_messages(user):

    # First send the intro message
    organisation = getattr(g, 'active_organisation', None) or user.default_organisation

    intro_message = i18n_for(
        user,
        "general_sms.welcome.{}".format(organisation.custom_welcome_message_key or 'generic'),
        first_name=user.first_name,
        balance=rounded_dollars(user.transfer_account.balance),
        token=user.transfer_account.token.name
    )

    send_message(user.phone, intro_message)

    send_terms_message_if_required(user)


def send_terms_message_if_required(user):

    if not user.seen_latest_terms:
        terms_message = i18n_for(user, "general_sms.terms")
        send_message(user.phone, terms_message)
        user.seen_latest_terms = True


def send_onboarding_message(to_phone, first_name, amount, currency_name, one_time_code):
    if to_phone:
        receiver_message = '{}, you have been registered for {}. You have {} {}. Your one-time code is {}. ' \
                           'Download Sempo for Android: https://bit.ly/2UVZLqf' \
            .format(
            first_name,
            current_app.config['PROGRAM_NAME'],
            amount if not None else 0,
            currency_name,
            one_time_code,
        )

        send_message(to_phone, receiver_message)


def send_phone_verification_message(to_phone, one_time_code):
    if to_phone:
        reciever_message = 'Your Sempo verification code is: {}'.format(one_time_code)
        send_message(to_phone, reciever_message)


def send_sms(user, message_key):
    message = i18n_for(user, "user.{}".format(message_key))
    send_message(user.phone, message)


def change_pin(user, new_pin):
    user.hash_pin(new_pin)
    user.delete_pin_reset_tokens()


def change_initial_pin(user: User, new_pin):
    user.is_activated = True
    change_pin(user, new_pin)


def change_current_pin(user: User, new_pin):
    change_pin(user, new_pin)


def admin_reset_user_pin(user: User):
    user.set_one_time_code(None)
    user.pin_hash = None

    pin_reset_token = user.encode_single_use_JWS('R')
    user.save_pin_reset_token(pin_reset_token)
    user.failed_pin_attempts = 0

def default_transfer_account(user: User) -> TransferAccount:
    if user.default_transfer_account is not None:
        return user.default_transfer_account
    else:
        raise TransferAccountNotFoundError("no default transfer account set")


def default_token(user: User) -> Token:
    try:
        transfer_account = default_transfer_account(user)
        token = transfer_account.token
    except TransferAccountNotFoundError:
        if user.default_organisation is not None:
            token = user.default_organisation.token
        else:
            token = Organisation.master_organisation().token

        if token is None:
            raise Exception('no default token for user')

    return token


def get_user_by_phone(phone: str, region: str, should_raise=False) -> Optional[User]:
    try:
        user = User.query.execution_options(show_all=True).filter_by(
            phone=proccess_phone_number(phone_number=phone, region=region)
        ).first()
    except NumberParseException as e:
        if should_raise:
            raise e
        else:
            return None

    if user is not None:
        return user
    else:
        if should_raise:
            raise Exception('User not found.')
        else:
            return None


def transfer_usages_for_user(user: User) -> List[TransferUsage]:
    most_common_uses = user.get_most_relevant_transfer_usages()

    def usage_sort(a, b):
        ma = most_common_uses.get(a.name)
        mb = most_common_uses.get(b.name)

        # return prioritied, then used, then everything else
        if a.priority and b.priority:
            if a.priority < b.priority:
                return -1
            else:
                return 1
        elif a.priority:
            return -1
        elif b.priority:
            return 1
        elif ma is not None and mb is not None:
            if ma >= mb:
                return -1
            else:
                return 1
        elif ma is not None:
            return -1
        elif mb is not None:
            return 1
        else:
            return -1

    ordered_transfer_usages = sorted(TransferUsage.query.all(), key=cmp_to_key(usage_sort))
    return ordered_transfer_usages

def create_transfer_account_if_required(blockchain_address, token, account_type=TransferAccountType.EXTERNAL):
    transfer_account = TransferAccount.query.execution_options(show_all=True).filter_by(blockchain_address=blockchain_address).first()
    if transfer_account:
        return transfer_account
    else:
        return TransferAccount(
            blockchain_address=blockchain_address,
            token=token,
            account_type=account_type
        )
