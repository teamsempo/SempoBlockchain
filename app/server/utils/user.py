import threading, re
from phonenumbers.phonenumberutil import NumberParseException
from sqlalchemy.orm.attributes import flag_modified
from bit import base58
from flask import current_app

from server import db, models
from server.schemas import user_schema
from server.constants import DEFAULT_ATTRIBUTES, KOBO_META_ATTRIBUTES, CREATE_USER_SETTINGS
from server.exceptions import NoTransferCardError
from server import celery_app, sentry
from server.utils import credit_transfers as CreditTransferUtils
from server.utils.phone import proccess_phone_number, send_onboarding_message
from server.utils.amazon_s3 import generate_new_filename, save_to_s3_from_url, LoadFileException
from server.utils.misc import elapsed_time

from ethereum import utils


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

        user = models.User.query.filter_by(email=str(public_identifier).lower()).first()
        if user:
            continue

        try:
            user = models.User.query.filter_by(phone=proccess_phone_number(public_identifier)).first()
            if user:
                continue
        except NumberParseException:
            pass

        user = models.User.query.filter_by(public_serial_number=str(public_identifier).lower()).first()
        if user:
            continue

        user = models.User.query.filter_by(nfc_serial_number=public_identifier.upper()).first()
        if user:
            continue

        try:
            checksummed = utils.checksum_encode(public_identifier)
            blockchain_address = models.BlockchainAddress.query.filter_by(address=checksummed).first()

            if blockchain_address and blockchain_address.transfer_account:
                user = blockchain_address.transfer_account.primary_user
                if user:
                    continue

        except Exception:
            pass

    return user


def get_transfer_card(public_serial_number):
    transfer_card = models.TransferCard.query.filter_by(
        public_serial_number=public_serial_number).first()

    if not transfer_card:
        raise NoTransferCardError("No transfer card found for public serial number {}"
                                  .format(public_serial_number))

    return transfer_card


def update_transfer_account_user(user,
                                 first_name=None, last_name=None,
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
    if phone:
        user.phone = phone
    if email:
        user.email = email
    if public_serial_number:
        user.public_serial_number = public_serial_number
    if location:
        user.location = location

    if use_precreated_pin:
        transfer_card = get_transfer_card(public_serial_number)

        user.set_pin(transfer_card.PIN)

    is_supervendor = True if is_vendor and not existing_transfer_account else False

    user.is_vendor = is_vendor
    user.is_beneficiary = is_beneficiary
    user.is_supervendor = is_supervendor

    if existing_transfer_account:
        user.transfer_account = existing_transfer_account

    return user


def create_transfer_account_user(first_name=None, last_name=None,
                                 phone=None, email=None, public_serial_number=None,
                                 blockchain_address=None,
                                 transfer_account_name=None,
                                 location=None,
                                 use_precreated_pin=False,
                                 use_last_4_digits_of_id_as_initial_pin = False,
                                 existing_transfer_account=None,
                                 is_beneficiary=False,
                                 is_vendor=False):

    user = models.User(first_name=first_name,
                       last_name=last_name,
                       phone=phone,
                       email=email,
                       public_serial_number=public_serial_number)

    precreated_pin = None
    is_activated = False

    if use_precreated_pin:
        transfer_card = get_transfer_card(public_serial_number)
        precreated_pin = transfer_card.PIN
        is_activated = True

    elif use_last_4_digits_of_id_as_initial_pin:
        precreated_pin = str(public_serial_number or phone)[-4:]
        is_activated = False

    user.set_pin(precreated_pin, is_activated)

    is_supervendor = True if is_vendor and not existing_transfer_account else False

    user.is_vendor = is_vendor
    user.is_beneficiary = is_beneficiary
    user.is_supervendor = is_supervendor

    db.session.add(user)

    if existing_transfer_account:
        user.transfer_account = existing_transfer_account
    else:

        transfer_account = models.TransferAccount(blockchain_address=blockchain_address)
        transfer_account.name = transfer_account_name
        transfer_account.location = location
        transfer_account.is_vendor = is_vendor

        user.transfer_account = transfer_account

    if current_app.config['AUTO_APPROVE_TRANSFER_ACCOUNTS']:
        user.transfer_account.approve()

    return user


def save_device_info(device_info, user):

    add_device = False

    if device_info['serialNumber'] and not models.DeviceInfo.query.filter_by(serial_number=device_info['serialNumber']).first():
        # Add the device if the serial number is defined, and isn't already in db
        add_device = True
    elif not device_info['serialNumber'] and not models.DeviceInfo.query.filter_by(unique_id=device_info['uniqueID']).first():
        # Otherwise add the device if the serial number is NOT defined unique id isn't already in db.
        # This means that where serial number is defined but unique id is different, we DO NOT add
        # (because unique ids can change under some circumstances, so they say)
        add_device = True

    if add_device:

        device = models.DeviceInfo()

        device.serial_number    = device_info['serialNumber']
        device.unique_id        = device_info['uniqueID']
        device.brand            = device_info['brand']
        device.model            = device_info['model']
        device.width            = device_info['width']
        device.height           = device_info['height']

        device.user = user

        db.session.add(device)

        return device


def set_custom_attributes(attribute_dict, user):
    default_attributes = {}
    custom_attributes = user.custom_attributes or {}   # loads in any existing custom attributes
    for key in attribute_dict.keys():
        if key[0] != '_':
            if key in DEFAULT_ATTRIBUTES:
                default_attributes[key] = attribute_dict[key]
            elif key not in KOBO_META_ATTRIBUTES:
                custom_attributes[key] = {
                    'value': attribute_dict[key]
                }

    attachments = attribute_dict.get('_attachments', [])

    for attachment in attachments:
        submitted_filename = attachment['filename'].split('/')[-1]
        for attribute in custom_attributes.keys():
            if submitted_filename == custom_attributes[attribute]['value']:
                type = 'custom_attribute_{}'.format(attribute)

                new_filename = generate_new_filename(submitted_filename, type, 'KOBO')

                uploaded_image = models.UploadedImage(filename=new_filename, image_type=type)

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

                custom_attributes[attribute]['value'] = new_filename
                custom_attributes[attribute]['uploaded_image_id'] = uploaded_image.id

                continue

    user.custom_attributes = custom_attributes

    return default_attributes, custom_attributes


def force_attribute_dict_keys_to_lowercase(attribute_dict):
    return dict(zip(map(str.lower, attribute_dict.keys()), attribute_dict.values()))

def apply_settings(attribute_dict):
    for setting in CREATE_USER_SETTINGS:
        if setting not in attribute_dict:
            stored_setting = models.Settings.query.filter_by(name=setting).first()

            if stored_setting is not None:
                attribute_dict[setting] = stored_setting.value

    return attribute_dict

def convert_yes_no_string_to_bool(test_string):
    if str(test_string).lower() in ["yes", "true"]:
        return True
    elif str(test_string).lower() in ["no", "false"]:
        return False
    else:
        return test_string

def truthy_all_dict_values(attribute_dict):
    return dict(zip(attribute_dict.keys(), map(convert_yes_no_string_to_bool, attribute_dict.values())))

def return_index_of_slash_or_neg1(string):
    try:
        return str(string).index("/")
    except ValueError:
        return -1


def remove_whitespace_from_string(maybe_string):
    if isinstance(maybe_string,str):
        return re.sub(r'[\t\n\r]', '', maybe_string)
    else:
        return maybe_string

def strip_kobo_preslashes(attribute_dict):
    return dict(zip(map(lambda key: key[return_index_of_slash_or_neg1(key) + 1:], attribute_dict.keys()), attribute_dict.values()))

def strip_whitespace_characters(attribute_dict):
    return dict(zip(map(remove_whitespace_from_string,attribute_dict.keys()), map(remove_whitespace_from_string, attribute_dict.values())))

def proccess_attribute_dict(attribute_dict,
                            force_dict_keys_lowercase=False,
                            allow_existing_user_modify=False,
                            require_transfer_card_exists=False):
    elapsed_time('1.0 Start')

    if force_dict_keys_lowercase:
        attribute_dict = force_attribute_dict_keys_to_lowercase(attribute_dict)

    attribute_dict = strip_kobo_preslashes(attribute_dict)

    attribute_dict = apply_settings(attribute_dict)

    attribute_dict = truthy_all_dict_values(attribute_dict)

    attribute_dict = strip_whitespace_characters(attribute_dict)

    elapsed_time('2.0 Post Processing')

    email = attribute_dict.get('email')
    phone = attribute_dict.get('phone')

    blockchain_address = attribute_dict.get('blockchain_address')

    provided_public_serial_number = attribute_dict.get('public_serial_number')

    if not blockchain_address and provided_public_serial_number:

        try:
            blockchain_address = utils.checksum_encode(provided_public_serial_number)

            # Since it's actually an ethereum address set the provided public serial number to None
            # so it doesn't get used as a transfer card
            provided_public_serial_number = None
        except Exception:
            pass

    public_serial_number = (provided_public_serial_number
                            or attribute_dict.get('payment_card_qr_code')
                            or attribute_dict.get('payment_card_barcode'))

    location = attribute_dict.get('location')

    use_precreated_pin = attribute_dict.get('use_precreated_pin')
    use_last_4_digits_of_id_as_initial_pin = attribute_dict.get('use_last_4_digits_of_id_as_initial_pin')

    transfer_account_name = attribute_dict.get('transfer_account_name')
    first_name = attribute_dict.get('first_name')
    last_name = attribute_dict.get('last_name')

    primary_user_identifier = attribute_dict.get('primary_user_identifier')
    primary_user_pin = attribute_dict.get('primary_user_pin')

    custom_initial_disbursement = attribute_dict.get('custom_initial_disbursement', None)

    is_vendor = attribute_dict.get('is_vendor', None)
    if is_vendor is None:
        is_vendor = attribute_dict.get('vendor', False)

    # is_beneficiary defaults to the opposite of is_vendor
    is_beneficiary = attribute_dict.get('is_beneficiary', not is_vendor)

    if current_app.config['IS_USING_BITCOIN']:
        try:
            base58.b58decode_check(blockchain_address)
        except ValueError:
            response_object = {'message': 'Blockchain Address {} Not Valid'.format(blockchain_address)}
            return response_object, 400

    if isinstance(phone,bool):
        phone = None

    if phone:
        try:
            phone = proccess_phone_number(phone)
        except NumberParseException as e:
            response_object = {'message': 'Invalid Phone Number: ' + str(e)}
            return response_object, 400

    # Work out if there's an existing transfer account to bind to
    existing_transfer_account = None
    if primary_user_identifier:

        primary_user = find_user_from_public_identifier(primary_user_identifier)

        if not primary_user or not primary_user.verify_password(primary_user_pin):
            response_object = {'message': 'Primary User not Found'}
            return response_object, 400

        if not primary_user.verify_password(primary_user_pin):

            response_object = {'message': 'Invalid PIN for Primary User'}
            return response_object, 400

        primary_user_transfer_account = primary_user.transfer_account

        if not primary_user_transfer_account:
            response_object = {'message': 'Primary User has no transfer account'}
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
            transfer_card = models.TransferCard.query.filter_by(
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

    existing_user = find_user_from_public_identifier(email, phone, public_serial_number, blockchain_address)
    if existing_user:

        if not allow_existing_user_modify:
            response_object = {'message': 'User already exists for Identifier'}
            return response_object, 400

        user = update_transfer_account_user(
            existing_user,
            first_name=first_name, last_name=last_name,
            phone=phone, email=email, public_serial_number=public_serial_number,
            use_precreated_pin=use_precreated_pin,
            existing_transfer_account=existing_transfer_account,
            is_beneficiary=is_beneficiary, is_vendor=is_vendor
            )

        default_attributes, custom_attributes = set_custom_attributes(attribute_dict, user)
        flag_modified(user, "custom_attributes")

        db.session.commit()

        response_object = {
            'message': 'User Updated',
            'data': {'user': user_schema.dump(user).data}
        }

        return response_object, 200

    elapsed_time('3.0 Ready to create')

    user = create_transfer_account_user(
        first_name=first_name, last_name=last_name,
        phone=phone, email=email, public_serial_number=public_serial_number,
        blockchain_address=blockchain_address,
        transfer_account_name=transfer_account_name,
        location=location,
        use_precreated_pin=use_precreated_pin,
        use_last_4_digits_of_id_as_initial_pin = use_last_4_digits_of_id_as_initial_pin,
        existing_transfer_account=existing_transfer_account,
        is_beneficiary=is_beneficiary, is_vendor=is_vendor
    )

    elapsed_time('4.0 Created')

    default_attributes, custom_attributes = set_custom_attributes(attribute_dict, user)

    if custom_initial_disbursement:
        try:
            disbursement = CreditTransferUtils.make_disbursement_transfer(custom_initial_disbursement, user)
        except Exception as e:
            response_object = {'message': str(e)}
            return response_object, 400

    elapsed_time('5.0 Disbursement done')

    db.session.flush()

    if location:
        user.location = location

    if phone and current_app.config['ONBOARDING_SMS']:
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
            pass

    if user.one_time_code:
        response_object = {
            'message': 'User Created',
            'data': {
                'user': user_schema.dump(user).data
            }
        }

    else:
        response_object = {
            'message': 'User Created',
            'data': {'user': user_schema.dump(user).data }
        }

    elapsed_time('6.0 Complete')

    return response_object, 200