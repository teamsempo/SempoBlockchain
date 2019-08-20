import hashlib
import hmac
import time

from flask import make_response, jsonify, current_app
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
import datetime, json

from server.exceptions import NoTransferAccountError, UserNotFoundError, InsufficientBalanceError, AccountNotApprovedError, \
    InvalidTargetBalanceError, BlockchainError
from server import db, celery_app, sentry, red
from server import models
from server.schemas import me_credit_transfer_schema
from server.utils import user as UserUtils
from server.utils import pusher
from server.utils.misc import elapsed_time

def calculate_transfer_stats(total_time_series=False):

    total_distributed = db.session.query(func.sum(models.CreditTransfer.transfer_amount).label('total'))\
        .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.DISBURSEMENT).first().total

    total_spent = db.session.query(func.sum(models.CreditTransfer.transfer_amount).label('total'))\
        .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.PAYMENT).first().total

    total_beneficiaries = db.session.query(models.User).filter(models.User.is_beneficiary == True).count()

    total_vendors = db.session.query(models.User)\
        .filter(models.User.is_vendor == True).count()

    total_users = total_beneficiaries + total_vendors

    has_transferred_count = db.session.query(func.count(func.distinct(models.CreditTransfer.sender_user_id))
        .label('transfer_count'))\
        .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.PAYMENT).first().transfer_count

    # zero_balance_count = db.session.query(func.count(models.TransferAccount.id).label('zero_balance_count'))\
    #     .filter(models.TransferAccount.balance == 0).first().zero_balance_count

    exhausted_balance_count = db.session.query(func.count(func.distinct(models.CreditTransfer.sender_transfer_account_id))
        .label('transfer_count')) \
        .join(models.CreditTransfer.sender_transfer_account)\
        .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.PAYMENT) \
        .filter(models.TransferAccount.balance == 0).first().transfer_count

    daily_transaction_volume = db.session.query(func.sum(models.CreditTransfer.transfer_amount).label('volume'),
                 func.date_trunc('day', models.CreditTransfer.created).label('date'))\
        .group_by(func.date_trunc('day', models.CreditTransfer.created))\
        .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.PAYMENT).all()

    daily_disbursement_volume = db.session.query(func.sum(models.CreditTransfer.transfer_amount).label('volume'),
                                                func.date_trunc('day', models.CreditTransfer.created).label('date')) \
        .group_by(func.date_trunc('day', models.CreditTransfer.created)) \
        .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.DISBURSEMENT).all()

    try:
        master_wallet_balance = master_wallet_funds_available()
    except BlockchainError:
        master_wallet_balance = 0


    try:
        last_day = daily_transaction_volume[0].date
        last_day_volume = daily_transaction_volume[0].volume
        transaction_vol_list = [
            {'date': item.date.isoformat(), 'volume': item.volume} for item in daily_transaction_volume
        ]
    except IndexError:  # No transactions
        last_day = datetime.datetime.utcnow()
        last_day_volume = 0
        has_transferred_count = 0
        transaction_vol_list = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]

    try:
        last_day_disbursement_volume = daily_disbursement_volume[0].volume
        disbursement_vol_list = [
            {'date': item.date.isoformat(), 'volume': item.volume} for item in daily_disbursement_volume
        ]
    except IndexError:
        last_day_disbursement_volume = 0
        disbursement_vol_list = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]

    data = {
        'total_distributed': total_distributed,
        'total_spent': total_spent,
        'has_transferred_count': has_transferred_count,
        'zero_balance_count': exhausted_balance_count,
        'total_beneficiaries': total_beneficiaries,
        'total_users': total_users,
        'master_wallet_balance': master_wallet_balance,
        'daily_transaction_volume': transaction_vol_list,
        'daily_disbursement_volume': disbursement_vol_list,
        'last_day_volume': {'date': last_day.isoformat(), 'volume': last_day_volume}
    }

    return data


def master_wallet_funds_available(allowed_cache_age_seconds=60):
    """
    IF refreshing cash THEN:
        return: [current blockchain balance] - [all transfers with blockchain state pending or unknown]
        save to cache: [funds available at last cache], [ID of highest transfer used in cache], [cache creation datetime]
    ELSE
        return: [funds available at last cache] - [all non-failed transfers since cache created]
    :param allowed_cache_age_seconds: how long between checking the blockchain for external funds added or removed
    :return: amount of funds available
    """


    refresh_cache = False
    funds_available_cache = red.get('funds_available_cache')

    try:
        parsed_cache = json.loads(funds_available_cache)

        last_updated_datetime = datetime.datetime.fromtimestamp(float(parsed_cache['last_updated']))

        earliest_allowed = datetime.datetime.utcnow() - datetime.timedelta(seconds=allowed_cache_age_seconds)
        if last_updated_datetime < earliest_allowed:
            refresh_cache = True

    except Exception as e:
        refresh_cache = True


    if refresh_cache:

        blockchain_task = celery_app.signature('worker.celery_tasks.get_master_balance')

        result = blockchain_task.apply_async()

        try:
            master_wallet_balance = result.wait(timeout=6, propagate=True, interval=0.5)

        except Exception as e:
            print(e)
            sentry.captureException()
            raise BlockchainError("Blockchain Error")

        finally:
            result.forget()

        highest_transfer_id_checked = 0
        required_blockchain_statuses = ['PENDING', 'UNKNOWN']

    else:
        cached_funds_available = parsed_cache['cached_funds_available']
        highest_transfer_id_checked = parsed_cache['highest_transfer_id_checked']
        required_blockchain_statuses = ['PENDING', 'UNKNOWN', 'COMPLETE']



    new_dibursements     = (models.CreditTransfer.query
                             .filter(models.CreditTransfer.transfer_type == models.TransferTypeEnum.DISBURSEMENT)
                             .filter(models.CreditTransfer.transfer_status == models.TransferStatusEnum.COMPLETE)
                             .filter(models.CreditTransfer.id > highest_transfer_id_checked)
                             .filter(models.CreditTransfer.created >
                                     datetime.datetime.utcnow() - datetime.timedelta(hours=36))
                             .all())


    local_disbursement_value = 0
    for disbursement in new_dibursements:

        status = disbursement.blockchain_status

        if status in required_blockchain_statuses:
            local_disbursement_value += disbursement.transfer_amount

    if refresh_cache:

        balance = master_wallet_balance - local_disbursement_value

        if len(new_dibursements) > 0:
            highest_transfer_id_checked = new_dibursements[-1].id
        else:
            all_transfers = models.CreditTransfer.query.all()
            if len(all_transfers) > 0:
                highest_transfer_id_checked = all_transfers[-1].id
            else:
                highest_transfer_id_checked = 0

        cache_data = {
            'cached_funds_available': balance,
            'highest_transfer_id_checked': highest_transfer_id_checked,
            'last_updated': datetime.datetime.utcnow().timestamp()
        }

        red.set('funds_available_cache', json.dumps(cache_data))

        balance = master_wallet_balance - local_disbursement_value

        return balance

    else:

        balance = cached_funds_available - local_disbursement_value

        return balance


def find_user_with_transfer_account_from_identifiers(user_id, public_identifier, transfer_account_id):

    user = find_user_from_identifiers(user_id, public_identifier, transfer_account_id)

    if user and not user.transfer_account:
        raise NoTransferAccountError('User {} does not have a transfer account'.format(user))

    return user


def find_user_from_identifiers(user_id, public_identifier, transfer_account_id):

    if user_id:
        user = models.User.query.get(user_id)

        if not user:
            raise UserNotFoundError('User not found for user id {}'.format(user_id))
        else:
            return user

    if public_identifier:
        user = UserUtils.find_user_from_public_identifier(public_identifier)

        if not user:
            raise UserNotFoundError('User not found for public identifier {}'.format(user_id))
        else:
            return user

    if transfer_account_id:
        transfer_account = models.TransferAccount.query.get(transfer_account_id)

        user = transfer_account.primary_user

        if not user:
            raise UserNotFoundError('User not found for public identifier {}'.format(user_id))
        else:
            return user

    return None

def create_and_commit_transfer(transfer_amount, send_account = None, receive_account = None, uuid=None):
    try:
        transfer = models.CreditTransfer(transfer_amount, sender=send_account, recipient=receive_account, uuid=uuid)

        # We need this commit to prevent a race condition with the async blockchain task
        db.session.commit()

    except IntegrityError:
        raise Exception("Transfer Integrity Error")

    return transfer


def handle_transfer_to_blockchain_address(
    transfer_amount, sender_user, recipient_blockchain_address, transfer_use, uuid=None):

    if transfer_amount > sender_user.transfer_account.balance:
        responseObject = {
            'message': 'Insufficient funds',
            'feedback': True,
        }
        return make_response(jsonify(responseObject)), 400

    try:
        transfer = make_blockchain_transfer(transfer_amount,
                                            sender_user.transfer_account.blockchain_address.address,
                                            recipient_blockchain_address,
                                            transfer_use,
                                            uuid=None)

        # This is the top-level commit for this flow
        db.session.commit()

    except AccountNotApprovedError as e:
        responseObject = {
            'message': "Sender is not approved",
            'feedback': True,
        }
        return make_response(jsonify(responseObject)), 400

    except InsufficientBalanceError as e:
        responseObject = {
            'message': "Insufficient balance",
            'feedback': True,
        }
        return make_response(jsonify(responseObject)), 400

    responseObject = {
        'message': 'Payment Successful',
        'feedback': True,
        'data': {
            'credit_transfer': me_credit_transfer_schema.dump(transfer).data
        }
    }

    return make_response(jsonify(responseObject)), 201

def create_address_object_if_required(address):
    address_obj = models.BlockchainAddress.query.filter_by(address=address).first()

    if not address_obj:
        address_obj = models.BlockchainAddress(type="EXTERNAL")
        address_obj.address = address

        db.session.add(address_obj)

    return address_obj


def make_blockchain_transfer(transfer_amount,
                             send_address,
                             receive_address,
                             transfer_use=None,
                             transfer_mode=None,
                             require_sender_approved=False,
                             require_sufficient_balance=False,
                             automatically_resolve_complete=True,
                             uuid=None,
                             existing_blockchain_txn=False
                             ):

    send_address_obj = create_address_object_if_required(send_address)
    receive_address_obj = create_address_object_if_required(receive_address)

    if send_address_obj.transfer_account:
        sender_user =  send_address_obj.transfer_account.primary_user
    else:
        sender_user = None

    if receive_address_obj.transfer_account:
        recipient_user = receive_address_obj.transfer_account.primary_user
    else:
        recipient_user = None

    require_recipient_approved = False
    transfer = make_payment_transfer(transfer_amount,
                                     sender_user,
                                     recipient_user,
                                     transfer_use,
                                     transfer_mode,
                                     require_sender_approved,
                                     require_recipient_approved,
                                     require_sufficient_balance,
                                     automatically_resolve_complete=False)

    transfer.sender_blockchain_address = send_address_obj
    transfer.recipient_blockchain_address = receive_address_obj

    transfer.transfer_type = models.TransferTypeEnum.PAYMENT

    if uuid:
        transfer.uuid = uuid

    if existing_blockchain_txn:
        existing_blockchain_txn_obj = models.BlockchainTransaction(
            status='SUCCESS',
            message='External Txn',
            added_date=datetime.datetime.utcnow(),
            hash=existing_blockchain_txn,
            transaction_type='transfer'
        )

        existing_blockchain_txn_obj.credit_transfer = transfer
        db.session.add(existing_blockchain_txn_obj)

    if automatically_resolve_complete:
        transfer.resolve_as_completed(existing_blockchain_txn=existing_blockchain_txn)

    pusher.push_admin_credit_transfer(transfer)

    return transfer

def make_payment_transfer(transfer_amount,
                          send_account,
                          receive_account,
                          transfer_use=None,
                          transfer_mode=None,
                          require_sender_approved=True,
                          require_recipient_approved=True,
                          require_sufficient_balance=True,
                          automatically_resolve_complete=True,
                          uuid=None):

    transfer = create_and_commit_transfer(transfer_amount,
                                          send_account=send_account,
                                          receive_account=receive_account,
                                          uuid=uuid)

    make_cashout_incentive_transaction = False

    if transfer_use is not None:
        usages = []
        try:
            use_ids = transfer_use.split(',')  # passed as '3,4' etc.
        except AttributeError:
            use_ids = transfer_use
        for use_id in use_ids:
            if use_id != 'null':
                use = models.TransferUsage.query.filter_by(id=use_id).first()
                if use:
                    usages.append(use.name)
                    if use.is_cashout:
                        make_cashout_incentive_transaction = True
                else:
                    usages.append('Other')

        transfer.transfer_use = usages

    transfer.transfer_mode = transfer_mode
    transfer.uuid = uuid

    if require_sender_approved and not transfer.check_sender_is_approved():
        message = "Sender {} is not approved".format(send_account)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=True)

    if require_recipient_approved and not transfer.check_recipient_is_approved():
        message = "Recipient {} is not approved".format(receive_account)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=False)

    if require_sufficient_balance and not transfer.check_sender_has_sufficient_balance():
        message = "Sender {} has insufficient balance".format(send_account)
        transfer.resolve_as_rejected(message)
        raise InsufficientBalanceError(message)

    if automatically_resolve_complete:
        transfer.resolve_as_completed()
        pusher.push_admin_credit_transfer(transfer)

    if make_cashout_incentive_transaction:
        try:
            incentive_amount = round(transfer_amount * current_app.config['CASHOUT_INCENTIVE_PERCENT'] / 100)

            make_disbursement_transfer(incentive_amount, receive_account)

        except Exception as e:
            print(e)
            sentry.captureException()

    return transfer

def make_withdrawal_transfer(transfer_amount,
                             send_account,
                             transfer_mode=None,
                             require_sender_approved=True,
                             require_sufficient_balance=True,
                             automatically_resolve_complete=True,
                             uuid=None):

    transfer = create_and_commit_transfer(transfer_amount, send_account=send_account, uuid=uuid)

    transfer.transfer_mode = transfer_mode

    if require_sender_approved and not transfer.check_sender_is_approved():
        message = "Sender {} is not approved".format(send_account)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=True)

    if require_sufficient_balance and not transfer.check_sender_has_sufficient_balance():
        message = "Sender {} has insufficient balance".format(send_account)
        transfer.resolve_as_rejected(message)
        raise InsufficientBalanceError(message)

    if automatically_resolve_complete:
        transfer.resolve_as_completed()
        pusher.push_admin_credit_transfer(transfer)

    return transfer


def make_disbursement_transfer(transfer_amount,
                               receive_account,
                               transfer_mode=None,
                               automatically_resolve_complete=True,
                               uuid=None):

    if current_app.config['USING_EXTERNAL_ERC20']:

        master_wallet_balance = master_wallet_funds_available()

        if transfer_amount > master_wallet_balance:
            message = "Master Wallet has insufficient funds"
            raise InsufficientBalanceError(message)

    elapsed_time('4.1: Retrieved Master Balance')

    if current_app.config['IS_USING_BITCOIN']:
        if transfer_amount < 1000 * 100:
            raise Exception("Minimum Transfer Amount is 1000 sat")

    transfer = create_and_commit_transfer(transfer_amount, receive_account=receive_account, uuid=uuid)

    transfer.transfer_mode = transfer_mode

    elapsed_time('4.3: Created and commited')

    if automatically_resolve_complete:
        transfer.resolve_as_completed()
        elapsed_time('4.4: Resolved as complete')

        pusher.push_admin_credit_transfer(transfer)

        elapsed_time('4.5: Pusher complete')

    return transfer

def make_target_balance_transfer(target_balance,
                                 target_user,
                                 transfer_mode=None,
                                 allow_withdrawal=False,
                                 require_target_user_approved=True,
                                 require_sufficient_balance=True,
                                 automatically_resolve_complete=True,
                                 uuid=None):

    if target_balance is None:
        raise InvalidTargetBalanceError("Target balance not provided")

    transfer_amount = target_balance - target_user.transfer_account.balance

    if transfer_amount < 0 and not allow_withdrawal:
        raise InvalidTargetBalanceError("Setting balance would force withdrawal")

    if transfer_amount < 0:
        transfer = make_withdrawal_transfer(transfer_amount,
                                            target_user,
                                            transfer_mode,
                                            require_sender_approved=require_target_user_approved,
                                            require_sufficient_balance=require_sufficient_balance,
                                            automatically_resolve_complete=automatically_resolve_complete,
                                            uuid=uuid)

    else:
        transfer = make_disbursement_transfer(transfer_amount,
                                              target_user,
                                              transfer_mode,
                                              automatically_resolve_complete=automatically_resolve_complete,
                                              uuid=uuid)

    return transfer


def transfer_credit_via_phone(send_phone, receive_phone, transfer_amount):

    transfer_amount = abs(transfer_amount)

    send_user = models.User.query.filter_by(phone=send_phone).first()
    if send_user is None:
        return {'status': 'Fail', 'message': "Can't send from phone number: " + send_phone}

    receive_user = models.User.query.filter_by(phone=receive_phone).first()
    if receive_user is None:
        return {'status': 'Fail', 'message': "Can't send to phone number: " + send_phone}

    if send_user.transfer_account.balance < transfer_amount:
        return {'status': 'Fail', 'message': "Insufficient Funds"}

    transfer = make_payment_transfer(transfer_amount, send_user, receive_user)

    return {
        'status': 'Success',
        'message': "Transfer Successful",
        'transfer_data': transfer
    }


def check_for_any_valid_hash(transfer_amount, user_secret, hash_to_check):
    # How many seconds each hash lasts for
    time_interval = 5
    # How far in seconds from current time a valid hash can be
    time_tolerance = 30

    current_unix_time = int(time.time() * 1000)

    t_backward = 0
    while t_backward <= time_tolerance:
        unix_time_to_check = current_unix_time - t_backward * 1000

        valid = check_hash(hash_to_check, transfer_amount, user_secret, unix_time_to_check, time_interval)

        if valid:
            return True

        t_backward += time_interval

    t_forward = 0
    while t_forward <= time_tolerance:
        unix_time_to_check = current_unix_time + t_forward * 1000

        valid = check_hash(hash_to_check, transfer_amount, user_secret, unix_time_to_check, time_interval)

        if valid:
            return True

        t_forward += time_interval

    return False


def check_hash(hash_to_check, transfer_amount, user_secret, unix_time, time_interval):
    hash_size = 6

    intervaled_time = int((unix_time - (unix_time % (time_interval * 1000))) / (time_interval * 1000))

    valid_hash = valid_hmac = False

    string_to_hash = str(transfer_amount) + str(user_secret or '') + str(intervaled_time)
    full_hashed_string = hashlib.sha256(string_to_hash.encode()).hexdigest()
    truncated_hashed_string = full_hashed_string[0: hash_size]
    valid_hash = truncated_hashed_string == hash_to_check

    hmac_message = str(transfer_amount) + str(intervaled_time)
    full_hmac_string = hmac.new(user_secret.encode(),hmac_message.encode(),hashlib.sha256).hexdigest()
    truncated_hmac_string = full_hmac_string[0: hash_size]
    valid_hmac = truncated_hmac_string == hash_to_check

    return valid_hash or valid_hmac