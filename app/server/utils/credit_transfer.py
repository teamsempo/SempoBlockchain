import hashlib
import hmac
import time
from flask import make_response, jsonify, current_app, g
from sqlalchemy.sql import func
import datetime, json
import sentry_sdk

from server.exceptions import (
    NoTransferAccountError,
    UserNotFoundError,
    InsufficientBalanceError,
    AccountNotApprovedError,
    InvalidTargetBalanceError,
    TransferAccountNotFoundError
)

from server import db, red, bt
from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount
from server.models.blockchain_address import BlockchainAddress
from server.models.credit_transfer import CreditTransfer
from server.models.blockchain_transaction import BlockchainTransaction
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.schemas import me_credit_transfer_schema
from server.utils import user as UserUtils
from server.utils import pusher
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferStatusEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import cast


def cents_to_dollars(amount_cents):
    return float(amount_cents) / 100


def dollars_to_cents(amount_dollars):
    return float(amount_dollars) * 100


def calculate_transfer_stats(total_time_series=False, start_date=None, end_date=None):

    date_filter = []
    filter_active = False
    if start_date is not None and end_date is not None:
        date_filter.append(CreditTransfer.created >= start_date)
        date_filter.append(CreditTransfer.created <= end_date)
        filter_active = True

    user_filter = []

    disbursement_filters = [
        CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
        CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
        CreditTransfer.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT]

    standard_payment_filters = [
        CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
        CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
        CreditTransfer.transfer_subtype == TransferSubTypeEnum.STANDARD
    ]

    exchanged_filters = [
        CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
        CreditTransfer.transfer_type == TransferTypeEnum.EXCHANGE,
        CreditTransfer.token == g.active_organisation.token
    ]

    beneficiary_filters = [User.has_beneficiary_role == True]
    vendor_filters = [User.has_vendor_role == True]

    exhaused_balance_filters = [
        CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
        TransferAccount._balance_wei == 0
    ]

    transfer_use_filters = [
        *standard_payment_filters,
        CreditTransfer.transfer_use.isnot(None),
    ]

    def calculate_transaction_totals():
        total_distributed = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))

        if user_filter:
            total_distributed \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)

        total_distributed = (total_distributed.filter(*disbursement_filters).filter(*date_filter).first().total) or 0


        total_spent = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
                
        if user_filter:
            total_spent \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)
        
        total_spent = (total_spent.filter(*standard_payment_filters).filter(*date_filter).first().total) or 0


        total_exchanged = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        
        if user_filter:
            total_exchanged \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)

        total_exchanged = (total_exchanged.filter(*exchanged_filters).filter(*date_filter).first().total) or 0
        

        return total_distributed, total_spent, total_exchanged

    def calculate_user_totals():
        total_beneficiaries = db.session.query(User).filter(*beneficiary_filters).count()
        total_vendors = db.session.query(User).filter(*vendor_filters).count()
        total_users = total_beneficiaries + total_vendors

        has_transferred_count = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id))
            .label('transfer_count'))\
            .filter(*standard_payment_filters) \
            .filter(*date_filter) \
                .first().transfer_count

        exhausted_balance_count = db.session.query(func.count(func.distinct(
            CreditTransfer.sender_transfer_account_id))
            .label('transfer_count')) \
            .join(CreditTransfer.sender_transfer_account)\
            .filter(*exhaused_balance_filters) \
            .filter(*date_filter) \
                .first().transfer_count

        return total_beneficiaries, total_vendors, total_users, has_transferred_count, exhausted_balance_count

    
    def calculate_daily_transaction_volume():

        daily_transaction_volume = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                                                    func.date_trunc('day', CreditTransfer.created).label('date'))

        if user_filter:
            daily_transaction_volume \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)

        daily_transaction_volume = daily_transaction_volume.group_by(func.date_trunc('day', CreditTransfer.created))\
            .filter(*standard_payment_filters) \
            .filter(*date_filter) \
                .all()

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

        return transaction_vol_list, last_day, last_day_volume

    def calculate_daily_disbursement_volume():
        daily_disbursement_volume = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                                                    func.date_trunc('day', CreditTransfer.created).label('date'))
        if user_filter:
            daily_disbursement_volume \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)

        daily_disbursement_volume = daily_disbursement_volume.group_by(func.date_trunc('day', CreditTransfer.created)) \
            .filter(*disbursement_filters) \
            .filter(*date_filter) \
                .all()

        try:
            last_day_disbursement_volume = daily_disbursement_volume[0].volume
            disbursement_vol_list = [
                {'date': item.date.isoformat(), 'volume': item.volume} for item in daily_disbursement_volume
            ]
        except IndexError:
            last_day_disbursement_volume = 0
            disbursement_vol_list = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]
        
        return disbursement_vol_list

    def calculate_transfer_use_breakdown():
        transfer_use_breakdown = db.session.query(CreditTransfer.transfer_use.cast(JSONB),func.count(CreditTransfer.transfer_use))

        if user_filter:
            transfer_use_breakdown \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)

        transfer_use_breakdown = transfer_use_breakdown.filter(*transfer_use_filters) \
            .group_by(CreditTransfer.transfer_use.cast(JSONB)) \
                .all()
        return transfer_use_breakdown
    
    def calculate_daily_transaction_average():
        daily_transaction_average = db.session.query(func.avg(CreditTransfer.transfer_amount).label('average'),func.date_trunc('day', CreditTransfer.created).label('date')) \
            
        if user_filter:
            daily_transaction_average \
                .join(User, CreditTransfer.sender_user_id == User.id) \
                .join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id) \
                .filter(*user_filter)

        daily_transaction_average = daily_transaction_average.group_by(func.date_trunc('day', CreditTransfer.created)) \
            .filter(*standard_payment_filters) \
            .filter(*date_filter) \
                .all()
                
        try:
            last_day_transaction_average = daily_transaction_average[0].average
            transaction_average_list = [
                {'date': item.date.isoformat(), 'average': item.average} for item in daily_transaction_average
            ]
        except IndexError:
            last_day_transaction_average = 0
            transaction_average_list = [{'date': datetime.datetime.utcnow().isoformat(), 'average': 0} ]

        return transaction_average_list

    try:
        master_wallet_balance = cached_funds_available()
    except:
        master_wallet_balance = 0

    daily_transaction_volume, last_day, last_day_volume = calculate_daily_transaction_volume()
    daily_disbursement_volume = calculate_daily_disbursement_volume()
    daily_transaction_average = calculate_daily_transaction_average()
    transfer_use_breakdown = calculate_transfer_use_breakdown()
    total_distributed, total_spent, total_exchanged = calculate_transaction_totals()
    total_beneficiaries, _, total_users, has_transferred_count, exhausted_balance_count = calculate_user_totals()


    data = {
        'total_distributed': total_distributed,
        'total_spent': total_spent,
        'total_exchanged': total_exchanged,
        'has_transferred_count': has_transferred_count,
        'zero_balance_count': exhausted_balance_count,
        'total_beneficiaries': total_beneficiaries,
        'total_users': total_users,
        'master_wallet_balance': master_wallet_balance,
        'daily_transaction_volume': daily_transaction_volume,
        'daily_disbursement_volume': daily_disbursement_volume,
        'daily_transaction_average': daily_transaction_average,
        'transfer_use_breakdown': transfer_use_breakdown,
        'last_day_volume': {'date': last_day.isoformat(), 'volume': last_day_volume},
        'filter_active': filter_active
    }

    return data


def cached_funds_available(allowed_cache_age_seconds=60):
    """
    IF refreshing cash THEN:
        return: [current blockchain balance] - [all transfers with blockchain state pending or unknown]
        save to cache: [funds available], [ID of highest transfer used in cache], [cache creation datetime]
    ELSE
        return: [funds available at last cache] - [all non-failed transfers since last cache]
    Max Txn ID is a simple way to determine whether txn was used in cache or not, and thus needs to be accounted for
    :param allowed_cache_age_seconds: how long between checking the blockchain for external funds added or removed
    :return: amount of funds available
    """
    token = g.active_organisation.org_level_transfer_account.token

    balance_wei = bt.get_wallet_balance(
        g.active_organisation.org_level_transfer_account.blockchain_address,
        token
    )

    return token.token_amount_to_system(balance_wei)

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

        master_wallet_balance = get_wallet_balance()

        highest_transfer_id_checked = 0
        required_blockchain_statuses = ['PENDING', 'UNKNOWN']

    else:
        cached_funds_available = parsed_cache['cached_funds_available']
        highest_transfer_id_checked = parsed_cache['highest_transfer_id_checked']
        required_blockchain_statuses = ['PENDING', 'UNKNOWN', 'COMPLETE']



    new_dibursements     = (CreditTransfer.query
                            .filter(CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT)
                            .filter(CreditTransfer.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT)
                            .filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
                            .filter(CreditTransfer.id > highest_transfer_id_checked)
                            .filter(CreditTransfer.created >
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
            all_transfers = CreditTransfer.query.all()
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

    if user and not user.transfer_accounts:
        raise NoTransferAccountError('User {} does not have a transfer account'.format(user))

    return user


def find_user_from_identifiers(user_id, public_identifier, transfer_account_id):

    if user_id:
        user = User.query.get(user_id)

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
        transfer_account = TransferAccount.query.get(transfer_account_id)

        user = transfer_account.primary_user

        if not user:
            raise UserNotFoundError('User not found for public identifier {}'.format(user_id))
        else:
            return user

    return None

def handle_transfer_to_blockchain_address(
    transfer_amount, sender_user, recipient_blockchain_address, transfer_use, uuid=None):

    if transfer_amount > sender_user.transfer_account.balance:
        response_object = {
            'message': 'Insufficient funds',
            'feedback': True,
        }
        return make_response(jsonify(response_object)), 400

    try:
        transfer = make_blockchain_transfer(transfer_amount,
                                            sender_user.transfer_account.blockchain_address.address,
                                            recipient_blockchain_address,
                                            transfer_use,
                                            uuid=None)

        # This is the top-level commit for this flow
        db.session.commit()

    except AccountNotApprovedError as e:
        response_object = {
            'message': "Sender is not approved",
            'feedback': True,
        }
        return make_response(jsonify(response_object)), 400

    except InsufficientBalanceError as e:
        response_object = {
            'message': "Insufficient balance",
            'feedback': True,
        }
        return make_response(jsonify(response_object)), 400

    response_object = {
        'message': 'Payment Successful',
        'feedback': True,
        'data': {
            'credit_transfer': me_credit_transfer_schema.dump(transfer).data
        }
    }

    return make_response(jsonify(response_object)), 201

def create_address_object_if_required(address):
    address_obj = BlockchainAddress.query.filter_by(address=address).first()

    if not address_obj:
        address_obj = BlockchainAddress(type="EXTERNAL")
        address_obj.address = address

        db.session.add(address_obj)

    return address_obj


def make_blockchain_transfer(transfer_amount,
                             send_address,
                             token,
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
                                     token,
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

    transfer.transfer_type = TransferTypeEnum.PAYMENT

    if uuid:
        transfer.uuid = uuid

    if existing_blockchain_txn:
        existing_blockchain_txn_obj = BlockchainTransaction(
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
                          token=None,
                          send_user=None,
                          send_transfer_account=None,
                          receive_user=None,
                          receive_transfer_account=None,
                          transfer_use=None,
                          transfer_mode=None,
                          require_sender_approved=True,
                          require_recipient_approved=True,
                          require_sufficient_balance=True,
                          automatically_resolve_complete=True,
                          uuid=None,
                          transfer_subtype: TransferSubTypeEnum=TransferSubTypeEnum.STANDARD,
                          is_ghost_transfer=False):
    """
    This is used for internal transfers between Sempo wallets.
    :param transfer_amount:
    :param token:
    :param send_user:
    :param send_transfer_account:
    :param receive_user:
    :param receive_transfer_account:
    :param transfer_use:
    :param transfer_mode:
    :param require_sender_approved:
    :param require_recipient_approved:
    :param require_sufficient_balance:
    :param automatically_resolve_complete:
    :param uuid:
    :param transfer_subtype: accepts TransferSubType str.
    :param is_ghost_transfer: if an account is created for recipient just to exchange, it's not real
    :return:
    """

    if transfer_subtype is TransferSubTypeEnum.DISBURSEMENT:
        require_sender_approved = False
        require_recipient_approved = False
        require_sufficient_balance = False
        # primary NGO wallet to disburse from
        send_transfer_account = receive_user.default_organisation.queried_org_level_transfer_account

    if transfer_subtype is TransferSubTypeEnum.RECLAMATION:
        require_sender_approved = False
        # primary NGO wallet to reclaim to
        receive_transfer_account = send_user.default_organisation.queried_org_level_transfer_account

    if transfer_subtype is TransferSubTypeEnum.INCENTIVE:
        send_transfer_account = receive_transfer_account.get_float_transfer_account()

    transfer = CreditTransfer(transfer_amount,
                              token=token,
                              sender_user=send_user,
                              sender_transfer_account=send_transfer_account,
                              recipient_user=receive_user,
                              recipient_transfer_account=receive_transfer_account,
                              uuid=uuid,
                              transfer_type=TransferTypeEnum.PAYMENT,
                              transfer_subtype=transfer_subtype,
                              is_ghost_transfer=is_ghost_transfer)

    make_cashout_incentive_transaction = False

    if transfer_use is not None:
        usages = []
        try:
            use_ids = transfer_use.split(',')  # passed as '3,4' etc.
        except AttributeError:
            use_ids = transfer_use
        for use_id in use_ids:
            if use_id != 'null':
                use = TransferUsage.query.get(int(use_id))
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
        message = "Sender {} is not approved".format(send_transfer_account)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=True)

    if require_recipient_approved and not transfer.check_recipient_is_approved():
        message = "Recipient {} is not approved".format(receive_user)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=False)

    if require_sufficient_balance and not transfer.check_sender_has_sufficient_balance():
        message = "Sender {} has insufficient balance".format(send_transfer_account)
        transfer.resolve_as_rejected(message)
        raise InsufficientBalanceError(message)

    if automatically_resolve_complete:
        transfer.resolve_as_completed()
        pusher.push_admin_credit_transfer(transfer)

    if make_cashout_incentive_transaction:
        try:
            # todo: check limits apply
            incentive_amount = round(transfer_amount * current_app.config['CASHOUT_INCENTIVE_PERCENT'] / 100)

            make_payment_transfer(
                incentive_amount,
                receive_user=receive_user,
                transfer_subtype=TransferSubTypeEnum.INCENTIVE
            )

        except Exception as e:
            print(e)
            sentry_sdk.capture_exception(e)

    return transfer


def make_withdrawal_transfer(transfer_amount,
                             token,
                             send_account,
                             transfer_mode=None,
                             require_sender_approved=True,
                             require_sufficient_balance=True,
                             automatically_resolve_complete=True,
                             uuid=None):
    """
    This is used for a user withdrawing funds from their Sempo wallet. Only interacts with Sempo float.
    :param transfer_amount:
    :param token:
    :param send_account:
    :param transfer_mode:
    :param require_sender_approved:
    :param require_sufficient_balance:
    :param automatically_resolve_complete:
    :param uuid:
    :return:
    """

    transfer = CreditTransfer(transfer_amount, token,
                              sender_user=send_account,
                              uuid=uuid, transfer_type=TransferTypeEnum.WITHDRAWAL)

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


def make_deposit_transfer(transfer_amount,
                          token,
                          receive_account,
                          transfer_mode=None,
                          automatically_resolve_complete=True,
                          uuid=None,
                          fiat_ramp=None):
    """
    This is used for a user depositing funds to their Sempo wallet. Only interacts with Sempo float.
    :param transfer_amount:
    :param token:
    :param receive_account:
    :param transfer_mode:
    :param automatically_resolve_complete:
    :param uuid:
    :param fiat_ramp: A FiatRamp Object to tie to credit transfer
    :return:
    """

    transfer = CreditTransfer(amount=transfer_amount,
                              token=token,
                              recipient_user=receive_account,
                              transfer_type=TransferTypeEnum.DEPOSIT, uuid=uuid, fiat_ramp=fiat_ramp)

    transfer.transfer_mode = transfer_mode

    if automatically_resolve_complete:
        transfer.resolve_as_completed()
        pusher.push_admin_credit_transfer(transfer)

    return transfer


def make_target_balance_transfer(target_balance,
                                 target_user,
                                 transfer_mode=None,
                                 require_target_user_approved=True,
                                 require_sufficient_balance=True,
                                 automatically_resolve_complete=True,
                                 uuid=None):
    if target_balance is None:
        raise InvalidTargetBalanceError("Target balance not provided")

    if target_user.transfer_account is None:
        raise TransferAccountNotFoundError('Transfer account not found')

    transfer_amount = target_balance - target_user.transfer_account.balance

    if transfer_amount < 0:
        transfer = make_payment_transfer(abs(transfer_amount),
                                         target_user.transfer_account.token,
                                         send_user=target_user,
                                         transfer_mode=transfer_mode,
                                         require_sender_approved=require_target_user_approved,
                                         require_recipient_approved=False,
                                         require_sufficient_balance=require_sufficient_balance,
                                         automatically_resolve_complete=automatically_resolve_complete,
                                         uuid=uuid,
                                         transfer_subtype=TransferSubTypeEnum.RECLAMATION)

    else:
        transfer = make_payment_transfer(transfer_amount,
                                         target_user.transfer_account.token,
                                         receive_user=target_user,
                                         transfer_mode=transfer_mode,
                                         automatically_resolve_complete=automatically_resolve_complete,
                                         uuid=uuid,
                                         transfer_subtype=TransferSubTypeEnum.DISBURSEMENT)

    return transfer


def transfer_credit_via_phone(send_phone, receive_phone, transfer_amount):

    transfer_amount = abs(transfer_amount)

    send_user = User.query.filter_by(phone=send_phone).first()
    if send_user is None:
        return {'status': 'Fail', 'message': "Can't send from phone number: " + send_phone}

    receive_user = User.query.filter_by(phone=receive_phone).first()
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


def check_for_any_valid_hash(transfer_amount, transfer_account_id, user_secret, hash_to_check):
    # How many seconds each hash lasts for
    time_interval = 5
    # How far in seconds from current time a valid hash can be
    time_tolerance = 30

    current_unix_time = int(time.time() * 1000)

    t_backward = 0
    while t_backward <= time_tolerance:
        unix_time_to_check = current_unix_time - t_backward * 1000

        valid = check_hash(hash_to_check, transfer_amount, transfer_account_id, user_secret, unix_time_to_check, time_interval)

        if valid:
            return True

        t_backward += time_interval

    t_forward = 0
    while t_forward <= time_tolerance:
        unix_time_to_check = current_unix_time + t_forward * 1000

        valid = check_hash(hash_to_check, transfer_amount, transfer_account_id, user_secret, unix_time_to_check, time_interval)

        if valid:
            return True

        t_forward += time_interval

    return False


def check_hash(hash_to_check, transfer_amount, transfer_account_id, user_secret, unix_time, time_interval):
    hash_size = 6

    intervaled_time = int((unix_time - (unix_time % (time_interval * 1000))) / (time_interval * 1000))

    valid_hash = valid_hmac = False

    string_to_hash = str(transfer_amount) + str(transfer_account_id) + str(user_secret or '') + str(intervaled_time)
    full_hashed_string = hashlib.sha256(string_to_hash.encode()).hexdigest()
    truncated_hashed_string = full_hashed_string[0: hash_size]
    valid_hash = truncated_hashed_string == hash_to_check

    hmac_message = str(transfer_amount) + str(intervaled_time)
    full_hmac_string = hmac.new(user_secret.encode(),hmac_message.encode(),hashlib.sha256).hexdigest()
    truncated_hmac_string = full_hmac_string[0: hash_size]
    valid_hmac = truncated_hmac_string == hash_to_check

    return valid_hash or valid_hmac