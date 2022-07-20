import hashlib
import hmac
from datetime import datetime, timedelta
import time
from flask import make_response, jsonify, current_app
import sentry_sdk
from decimal import Decimal

from server.exceptions import (
    NoTransferAccountError,
    UserNotFoundError,
    InsufficientBalanceError,
    AccountNotApprovedError,
    InvalidTargetBalanceError,
    TransferAccountNotFoundError
)

from server import db
from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount
from server.models.blockchain_address import BlockchainAddress
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.schemas import me_credit_transfer_schema
from server.utils import user as UserUtils
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferModeEnum, BlockchainStatus
from server.utils.user import create_transfer_account_if_required


def cents_to_dollars(amount_cents):
    return Decimal(amount_cents) / 100


def dollars_to_cents(amount_dollars):
    return Decimal(amount_dollars) * 100

def find_user_with_transfer_account_from_identifiers(user_id, public_identifier, transfer_account_id):

    user, transfer_card = find_user_from_identifiers(user_id, public_identifier, transfer_account_id)

    if user and not user.transfer_accounts:
        raise NoTransferAccountError('User {} does not have a transfer account'.format(user))

    return user, transfer_card


def find_user_from_identifiers(user_id, public_identifier, transfer_account_id):

    if user_id:
        user = User.query.get(user_id)

        if not user:
            raise UserNotFoundError('User not found for user id {}'.format(user_id))
        else:
            return user, None

    if public_identifier:
        user, transfer_card = UserUtils.find_user_from_public_identifier(public_identifier)

        if not user:
            raise UserNotFoundError('User not found for public identifier {}'.format(user_id))
        else:
            return user, transfer_card

    if transfer_account_id:
        transfer_account = TransferAccount.query.get(transfer_account_id)

        user = transfer_account.primary_user

        if not user:
            raise UserNotFoundError('User not found for public identifier {}'.format(user_id))
        else:
            return user, None

    return None, None

def handle_transfer_to_blockchain_address(
        transfer_amount, sender_transfer_account, recipient_blockchain_address, transfer_use, transfer_mode, uuid=None):

    if transfer_amount > sender_transfer_account.balance:
        response_object = {
            'message': 'Insufficient funds',
            'feedback': True,
        }
        return make_response(jsonify(response_object)), 400

    try:
        transfer = make_blockchain_transfer(transfer_amount,
                                            sender_transfer_account.token,
                                            sender_transfer_account.blockchain_address,
                                            recipient_blockchain_address,
                                            transfer_use,
                                            transfer_mode,
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
                             token,
                             send_address,
                             receive_address,
                             transfer_use=None,
                             transfer_mode=None,
                             require_sender_approved=False,
                             require_sufficient_balance=False,
                             automatically_resolve_complete=True,
                             uuid=None,
                             existing_blockchain_txn=False,
                             transfer_type=TransferTypeEnum.PAYMENT
                             ):


    sender_transfer_account = create_transfer_account_if_required(send_address, token)
    recipient_transfer_account = create_transfer_account_if_required(receive_address, token)

    sender_user = sender_transfer_account.primary_user
    recipient_user = recipient_transfer_account.primary_user

    require_recipient_approved = False
    transfer = make_payment_transfer(transfer_amount=transfer_amount,
                                     token=token,
                                     send_transfer_account=sender_transfer_account,
                                     receive_transfer_account=recipient_transfer_account,
                                     send_user=sender_user,
                                     receive_user=recipient_user,
                                     transfer_use=transfer_use,
                                     transfer_mode=transfer_mode,
                                     require_sender_approved=require_sender_approved,
                                     require_recipient_approved=require_recipient_approved,
                                     require_sufficient_balance=require_sufficient_balance,
                                     automatically_resolve_complete=False)

    transfer.transfer_type = transfer_type

    if uuid:
        transfer.uuid = uuid

    if automatically_resolve_complete:
        transfer.resolve_as_complete()

    return transfer


def make_payment_transfer(
        transfer_amount,
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
        is_ghost_transfer=False,
        queue='high-priority',
        batch_uuid=None,
        transfer_type=TransferTypeEnum.PAYMENT,
        transfer_card=None
):
    """
    This is used for internal transfers between Sempo wallets.
    :param transfer_amount:
    :param token:
    :param send_user:
    :param send_transfer_account:
    :param receive_user:
    :param receive_transfer_account:
    :param transfer_use:
    :param transfer_mode: TransferModeEnum
    :param require_sender_approved:
    :param require_recipient_approved:
    :param require_sufficient_balance:
    :param automatically_resolve_complete:
    :param uuid:
    :param transfer_subtype: accepts TransferSubType str.
    :param is_ghost_transfer: if an account is created for recipient just to exchange, it's not real
    :param queue:
    :param batch_uuid:
    :param transfer_type: the type of transfer
    :param transfer_card: the card that was used to make the payment
    :return:
    """
    if transfer_subtype is TransferSubTypeEnum.DISBURSEMENT:
        require_sender_approved = False
        require_recipient_approved = False
        # primary NGO wallet to disburse from
        send_transfer_account = send_transfer_account or receive_user.default_organisation.queried_org_level_transfer_account

    if transfer_subtype is TransferSubTypeEnum.RECLAMATION:
        require_sender_approved = False
        # primary NGO wallet to reclaim to
        receive_transfer_account = send_user.default_organisation.queried_org_level_transfer_account

    if transfer_subtype is TransferSubTypeEnum.INCENTIVE:
        send_transfer_account = send_transfer_account or receive_transfer_account.token.float_account

    transfer = CreditTransfer(transfer_amount,
                              token=token,
                              sender_user=send_user,
                              sender_transfer_account=send_transfer_account,
                              recipient_user=receive_user,
                              recipient_transfer_account=receive_transfer_account,
                              uuid=uuid,
                              transfer_type=transfer_type,
                              transfer_subtype=transfer_subtype,
                              transfer_mode=transfer_mode,
                              transfer_card=transfer_card,
                              is_ghost_transfer=is_ghost_transfer,
                              require_sufficient_balance=require_sufficient_balance)

    make_cashout_incentive_transaction = False

    if transfer_use is not None:
        for use_id in transfer_use:
            if use_id != 'null':
                use = TransferUsage.query.get(int(use_id))
                if use:
                    transfer.transfer_usages.append(use)
                    if use.is_cashout:
                        make_cashout_incentive_transaction = True
                else:
                    raise Exception(f'{use_id} not a valid transfer usage')

    transfer.uuid = uuid

    if require_sender_approved and not transfer.check_sender_is_approved():
        message = "Sender {} is not approved".format(send_transfer_account)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=True)

    if require_recipient_approved and not transfer.check_recipient_is_approved():
        message = "Recipient {} is not approved".format(receive_user)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=False)


    if automatically_resolve_complete:
        transfer.resolve_as_complete_and_trigger_blockchain(queue=queue, batch_uuid=batch_uuid)


    if make_cashout_incentive_transaction:
        try:
            # todo: check limits apply
            incentive_amount = round(transfer_amount * current_app.config['CASHOUT_INCENTIVE_PERCENT'] / 100)

            make_payment_transfer(
                incentive_amount,
                receive_user=receive_user,
                transfer_subtype=TransferSubTypeEnum.INCENTIVE,
                transfer_mode=TransferModeEnum.INTERNAL
            )

        except Exception as e:
            print(e)
            sentry_sdk.capture_exception(e)

    return transfer


def make_withdrawal_transfer(transfer_amount,
                             token,
                             send_user=None,
                             sender_transfer_account=None,
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

    transfer = CreditTransfer(
        transfer_amount,
        token,
        sender_user=send_user,
        sender_transfer_account=sender_transfer_account,
        uuid=uuid,
        transfer_type=TransferTypeEnum.WITHDRAWAL,
        transfer_mode=transfer_mode,
        require_sufficient_balance=require_sufficient_balance
    )

    if require_sender_approved and not transfer.check_sender_is_approved():
        message = "Sender {} is not approved".format(sender_transfer_account)
        transfer.resolve_as_rejected(message)
        raise AccountNotApprovedError(message, is_sender=True)

    if automatically_resolve_complete:
        transfer.resolve_as_complete_and_trigger_blockchain()

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
                              transfer_type=TransferTypeEnum.DEPOSIT, transfer_mode=transfer_mode,
                              uuid=uuid,
                              fiat_ramp=fiat_ramp,
                              require_sufficient_balance=False)

    if automatically_resolve_complete:
        transfer.resolve_as_complete_and_trigger_blockchain()

    return transfer


def make_target_balance_transfer(target_balance,
                                 target_user,
                                 transfer_mode=None,
                                 require_target_user_approved=True,
                                 require_sufficient_balance=True,
                                 automatically_resolve_complete=True,
                                 uuid=None,
                                 queue='high-priority'):
    if target_balance is None:
        raise InvalidTargetBalanceError("Target balance not provided")

    if target_user.transfer_account is None:
        raise TransferAccountNotFoundError('Transfer account not found')

    transfer_amount = Decimal(target_balance) - target_user.transfer_account.balance

    if transfer_amount == 0:
        raise InvalidTargetBalanceError("Transfer Amount can't be zero")

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
                                         transfer_subtype=TransferSubTypeEnum.RECLAMATION,
                                         queue=queue)

    else:
        transfer = make_payment_transfer(transfer_amount,
                                         target_user.transfer_account.token,
                                         receive_user=target_user,
                                         transfer_mode=transfer_mode,
                                         automatically_resolve_complete=automatically_resolve_complete,
                                         uuid=uuid,
                                         transfer_subtype=TransferSubTypeEnum.DISBURSEMENT,
                                         queue=queue)

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

    transfer = make_payment_transfer(transfer_amount, send_user, receive_user, transfer_mode=TransferModeEnum.SMS)

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

    hmac_message = str(transfer_amount) + str(transfer_account_id) + str(intervaled_time)

    full_hmac_string = hmac.new(
        user_secret.encode(),
        hmac_message.encode(),
        hashlib.sha256
    ).hexdigest()

    truncated_hmac_string = full_hmac_string[0: hash_size]
    valid_hmac = truncated_hmac_string == hash_to_check
    return truncated_hmac_string == hash_to_check

def _check_recent_transaction_sync_status(interval_time, time_to_error):
    # For interval_time = 5s, and time_to_error = 1 hour:
    # We want the start_time to be 1:00:05 ago
    # We want the end_time to be 1:00:00 ago
    # It's a rolling window in the past from between when something becomes an error, and when we last checked
    start_time = datetime.utcnow() - timedelta(seconds = interval_time) - timedelta(seconds = time_to_error)
    end_time = datetime.utcnow() - timedelta(seconds = time_to_error)

    transactions_in_window = CreditTransfer.query\
        .filter(CreditTransfer.updated >= start_time, CreditTransfer.updated <= end_time)\
        .execution_options(show_all=True)
    
    # Narrow down to transactions which weren't third party synchronized, but were
    # first party synchronized
    failed_transactions = transactions_in_window\
        .filter(CreditTransfer.received_third_party_sync == False)\
        .filter(CreditTransfer.blockchain_status == BlockchainStatus.SUCCESS)\
        .all()
    
    if failed_transactions:
        raise Exception(f'Warning! The following transactions were successfully completed, but did not appear in third party sync: {failed_transactions}')
    
    return failed_transactions
    
# Checks to see if any transactions within a certian window should have received a third 
# party transaction sync, but have not yet. 
def check_recent_transaction_sync_status(interval_time, time_to_error):
    # Create app and get context, since this is running in new background processes on a timer!
    from server import create_app
    app = create_app(skip_create_filters=True)
    with app.app_context():
        _check_recent_transaction_sync_status(interval_time, time_to_error)
