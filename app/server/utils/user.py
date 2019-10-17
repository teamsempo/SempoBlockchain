import threading
from phonenumbers.phonenumberutil import NumberParseException
from sqlalchemy.orm.attributes import flag_modified
from bit import base58
from flask import current_app
from eth_utils import to_checksum_address

from server import db
from server.models.device_info import DeviceInfo
from server.models.upload import UploadedImage
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.transfer_card import TransferCard
from server.models.transfer_account import TransferAccount
from server.models.blockchain_address import BlockchainAddress
from server.schemas import user_schema
from server.constants import DEFAULT_ATTRIBUTES, KOBO_META_ATTRIBUTES
from server.exceptions import PhoneVerificationError
from server import celery_app, sentry
from server.utils import credit_transfers as CreditTransferUtils
from server.utils.phone import proccess_phone_number, send_onboarding_message, send_phone_verification_message
from server.utils.amazon_s3 import generate_new_filename, save_to_s3_from_url, LoadFileException


def save_photo_and_check_for_duplicate(url, new_filename, image_id):

    save_to_s3_from_url(url, new_filename)

    try:
        rekognition_task = celery_app.signature('worker.celery_tasks.check_for_duplicate_person',
                                                args=(new_filename, image_id))

        rekognition_task.delay()
    except Exception as e:
        print(e)
        sentry.captureException()
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

    user = None

    for public_identifier in public_identifiers:

        if public_identifier is None:
            continue

        user = User.query.execution_options(show_all=True).filter_by(
            email=str(public_identifier).lower()).first()
        if user:
            continue

        try:
            user = User.query.execution_options(show_all=True).filter_by(
                phone=proccess_phone_number(public_identifier)).first()
            if user:
                continue
        except NumberParseException:
            pass

        user = User.query.execution_options(show_all=True).filter_by(
            public_serial_number=str(public_identifier).lower()).first()
        if user:
            continue

        user = User.query.execution_options(show_all=True).filter_by(
            nfc_serial_number=public_identifier.upper()).first()
        if user:
            continue

        try:
            checksummed = to_checksum_address(public_identifier)
            blockchain_address = BlockchainAddress.query.filter_by(
                address=checksummed).first()

            if blockchain_address and blockchain_address.transfer_account:
                user = blockchain_address.transfer_account.primary_user
                if user:
                    continue

        except Exception:
            pass

    return user


def update_transfer_account_user(user,
                                 first_name=None, last_name=None, preferred_language=None,
                                 phone=None, email=None, public_serial_number=None,
                                 location=None,
                                 use_precreated_pin=False,
                                 existing_transfer_account=None,
                                 is_beneficiary=False,
                                 is_vendor=False):

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
    if location:
        user.location = location

    if use_precreated_pin:
        transfer_card = TransferCard.get_transfer_card(public_serial_number)

        user.set_pin(transfer_card.PIN)

    if not is_vendor:
        vendor_tier = None
    elif existing_transfer_account:
        vendor_tier = 'vendor'
    else:
        vendor_tier = 'supervendor'

    user.set_held_role('VENDOR', vendor_tier)

    if is_beneficiary:
        user.set_held_role('BENEFICIARY', 'beneficiary')

    if existing_transfer_account:
        user.transfer_accounts.append(existing_transfer_account)

    return user


def create_transfer_account_user(first_name=None, last_name=None, preferred_language=None,
                                 phone=None, email=None, public_serial_number=None,
                                 organisation=None,
                                 token=None,
                                 blockchain_address=None,
                                 transfer_account_name=None,
                                 location=None,
                                 use_precreated_pin=False,
                                 use_last_4_digits_of_id_as_initial_pin=False,
                                 existing_transfer_account=None,
                                 is_beneficiary=False,
                                 is_vendor=False,
                                 is_self_sign_up=False):

    user = User(first_name=first_name,
                last_name=last_name,
                preferred_language=preferred_language,
                phone=phone,
                email=email,
                public_serial_number=public_serial_number,
                is_self_sign_up=is_self_sign_up)

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

    if not is_vendor:
        vendor_tier = None
    elif existing_transfer_account:
        vendor_tier = 'vendor'
    else:
        vendor_tier = 'supervendor'

    user.set_held_role('VENDOR', vendor_tier)

    if is_beneficiary:
        user.set_held_role('BENEFICIARY', 'beneficiary')

    if organisation:
        user.organisations.append(organisation)

    db.session.add(user)

    if existing_transfer_account:
        user.transfer_accounts.append(existing_transfer_account)
    else:

        transfer_account = TransferAccount(
            blockchain_address=blockchain_address, organisation=organisation)
        transfer_account.name = transfer_account_name
        transfer_account.location = location
        transfer_account.is_vendor = is_vendor
        user.transfer_accounts.append(transfer_account)

        if transfer_card:
            transfer_account.transfer_card = transfer_card

        if token:
            transfer_account.token = token

        if current_app.config['AUTO_APPROVE_TRANSFER_ACCOUNTS'] and not is_self_sign_up:
            transfer_account.approve()

    return user


def save_device_info(device_info, user):

    add_device = False

    if device_info['serialNumber'] and not DeviceInfo.query.filter_by(serial_number=device_info['serialNumber']).first():
        # Add the device if the serial number is defined, and isn't already in db
        add_device = True
    elif not device_info['serialNumber'] and not DeviceInfo.query.filter_by(unique_id=device_info['uniqueId']).first():
        # Otherwise add the device if the serial number is NOT defined unique id isn't already in db.
        # This means that where serial number is defined but unique id is different, we DO NOT add
        # (because unique ids can change under some circumstances, so they say)
        add_device = True

    if add_device:

        device = DeviceInfo()

        device.serial_number = device_info['serialNumber']
        device.unique_id = device_info['uniqueId']
        device.brand = device_info['brand']
        device.model = device_info['model']
        device.width = device_info['width']
        device.height = device_info['height']

        device.user = user

        db.session.add(device)

        return device


def extract_kobo_custom_attributes(post_data):
    custom_attributes = {}
    for key in post_data.keys():
        if key[0] != '_':
            if key not in KOBO_META_ATTRIBUTES and key not in DEFAULT_ATTRIBUTES:
                custom_attributes[key] = post_data[key]
    post_data['custom_attributes'] = custom_attributes
    return post_data


def set_custom_attributes(attribute_dict, user):
    # loads in any existing custom attributes
    custom_attributes = user.custom_attributes or {}
    for key in attribute_dict['custom_attributes'].keys():
        custom_attribute = CustomAttributeUserStorage(
            name=key, value=attribute_dict['custom_attributes'][key])
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

                uploaded_image = UploadedImage(
                    filename=new_filename, image_type=type)

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


def send_one_time_code(phone, user):
    try:
        send_phone_verification_message(
            to_phone=phone, one_time_code=user.one_time_code)

    except Exception as e:
        raise PhoneVerificationError(
            'Something went wrong. ERROR: {}'.format(e))


def proccess_create_or_modify_user_request(attribute_dict,
                                           organisation=None,
                                           allow_existing_user_modify=False,
                                           is_self_sign_up=False):
    """
    Takes a create or modify user request and determines the response. Normally what's in the top level API function,
    but here it's one layer down because there's multiple entry points for 'create user':
    - The admin api
    - The register api

    :param attribute_dict: attributes that can be supplied by the request maker
    :param organisation:  what organisation the request maker belongs to. The created user is bound to the same org
    :param allow_existing_user_modify: whether to return and error when the user already exists for the supplied IDs
    :param is_self_sign_up: does the request come from the register api?
    :return: An http response
    """

    email = attribute_dict.get('email')
    phone = attribute_dict.get('phone')

    blockchain_address = attribute_dict.get('blockchain_address')

    provided_public_serial_number = attribute_dict.get('public_serial_number')

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
        'require_transfer_card_exists', True)

    public_serial_number = (provided_public_serial_number
                            or attribute_dict.get('payment_card_qr_code')
                            or attribute_dict.get('payment_card_barcode'))

    location = attribute_dict.get('location')

    use_precreated_pin = attribute_dict.get('use_precreated_pin')
    use_last_4_digits_of_id_as_initial_pin = attribute_dict.get(
        'use_last_4_digits_of_id_as_initial_pin')

    transfer_account_name = attribute_dict.get('transfer_account_name')
    first_name = attribute_dict.get('first_name')
    last_name = attribute_dict.get('last_name')
    preferred_language = attribute_dict.get(
        'preferred_language')

    primary_user_identifier = attribute_dict.get('primary_user_identifier')
    primary_user_pin = attribute_dict.get('primary_user_pin')

    custom_initial_disbursement = attribute_dict.get(
        'custom_initial_disbursement', None)

    is_vendor = attribute_dict.get('is_vendor', None)
    if is_vendor is None:
        is_vendor = attribute_dict.get('vendor', False)

    # is_beneficiary defaults to the opposite of is_vendor
    is_beneficiary = attribute_dict.get('is_beneficiary', not is_vendor)

    if current_app.config['IS_USING_BITCOIN']:
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

        primary_user = find_user_from_public_identifier(
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

    if not (phone or email or public_serial_number or blockchain_address):
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

    if custom_initial_disbursement and not custom_initial_disbursement <= current_app.config['MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT']:
        response_object = {
            'message': 'Disbursement more than maximum allowed amount ({} {})'
            .format(current_app.config['MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT']/100, current_app.config['CURRENCY_NAME'])
        }
        return response_object, 400

    existing_user = find_user_from_public_identifier(
        email, phone, public_serial_number, blockchain_address)

    if existing_user:

        if not allow_existing_user_modify:
            response_object = {'message': 'User already exists for Identifier'}
            return response_object, 400

        user = update_transfer_account_user(
            existing_user,
            first_name=first_name, last_name=last_name, preferred_language=preferred_language,
            phone=phone, email=email, public_serial_number=public_serial_number,
            use_precreated_pin=use_precreated_pin,
            existing_transfer_account=existing_transfer_account,
            is_beneficiary=is_beneficiary, is_vendor=is_vendor
        )

        custom_attributes = set_custom_attributes(
            attribute_dict, user)
        flag_modified(user, "custom_attributes")

        db.session.commit()

        response_object = {
            'message': 'User Updated',
            'data': {'user': user_schema.dump(user).data}
        }

        return response_object, 200

    user = create_transfer_account_user(
        first_name=first_name, last_name=last_name, preferred_language=preferred_language,
        phone=phone, email=email, public_serial_number=public_serial_number,
        organisation=organisation,
        blockchain_address=blockchain_address,
        transfer_account_name=transfer_account_name,
        location=location,
        use_precreated_pin=use_precreated_pin,
        use_last_4_digits_of_id_as_initial_pin=use_last_4_digits_of_id_as_initial_pin,
        existing_transfer_account=existing_transfer_account,
        is_beneficiary=is_beneficiary, is_vendor=is_vendor, is_self_sign_up=is_self_sign_up
    )

    custom_attributes = set_custom_attributes(
        attribute_dict, user)

    if is_self_sign_up and attribute_dict.get('deviceinfo', None) is not None:
        save_device_info(device_info=attribute_dict.get(
            'deviceinfo'), user=user)

    if custom_initial_disbursement:
        disbursement = CreditTransferUtils.make_disbursement_transfer(
            custom_initial_disbursement, organisation.token, user)

    # Location fires an async task that needs to know user ID
    db.session.flush()

    if location:
        user.location = location

    if phone:
        if is_self_sign_up:
            send_one_time_code(phone=phone, user=user)
            return {'message': 'User Created. Please verify phone number.', 'otp_verify': True}, 200

        elif current_app.config['ONBOARDING_SMS']:
            try:
                balance = user.transfer_account.balance
                if isinstance(balance, int):
                    balance = balance / 100

                send_onboarding_message(
                    first_name=user.first_name,
                    to_phone=phone,
                    credits=balance,
                    one_time_code=user.one_time_code
                )
            except Exception as e:
                print(e)
                sentry.captureException()
                pass

    response_object = {
        'message': 'User Created',
        'data': {
            'user': user_schema.dump(user).data
        }
    }

    return response_object, 200
