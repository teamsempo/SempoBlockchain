import datetime
from typing import Optional

from server import db, message_processor
from server.exceptions import TransactionPercentLimitError, TransactionCountLimitError
from server.models.credit_transfer import CreditTransfer
from server.models.exchange import Exchange
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.utils.credit_transfer import make_payment_transfer
from server.utils.i18n import i18n_for
from server.models.user import User
from server.utils.user import default_token, default_transfer_account
from server.utils.credit_transfer import cents_to_dollars


class TokenProcessor(object):

    @staticmethod
    def format_amount(amount):
        return str(round(cents_to_dollars(amount), 2))

    @staticmethod
    def send_sms(user, message_key, **kwargs):
        # if we use token processor similarly for other countries later, can generalize country to init
        message = i18n_for(user, "ussd.kenya.{}".format(message_key), **kwargs)
        message_processor.send_message(user.phone, message)

    @staticmethod
    def send_success_sms(message_key: str, user: User, other_user: User, amount: float, reason: str, tx_time: datetime,
                         balance: float):

        amount_dollars = TokenProcessor.format_amount(amount)
        rounded_balance_dollars = TokenProcessor.format_amount(balance)

        TokenProcessor.send_sms(user, message_key, amount=amount_dollars, token_name=default_token(user).symbol,
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'), reason=reason,
                                time=tx_time.strftime('%I:%M %p'), balance=rounded_balance_dollars)

    @staticmethod
    def exchange_success_sms(message_key: str, user: User, other_user: User, own_amount: float, other_amount: float,
                             tx_time: datetime, balance: float):
        rounded_own_amount = str(round(own_amount, 2))
        rounded_other_amount = str(round(other_amount, 2))
        rounded_balance = str(round(balance, 2))
        TokenProcessor.send_sms(user, message_key, own_amount=rounded_own_amount, other_amount=rounded_other_amount,
                                own_token_name=default_token(user).symbol, other_token_name=default_token(other_user).symbol,
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'),
                                time=tx_time.strftime('%I:%M %p'), balance=rounded_balance)

    @staticmethod
    def get_balance(user: User):
        return TokenProcessor.balance_for_transfer_account(default_transfer_account(user))

    @staticmethod
    def balance_for_transfer_account(transfer_account: TransferAccount):
        # convert what comes back out from backend to dollars
        return transfer_account.balance / 100

    @staticmethod
    def get_limit(user: User, token: Token) -> Optional[TransferLimit]:
        example_transfer = CreditTransfer(transfer_type='EXCHANGE', sender_user=user, recipient_user=user, token=token, amount=0)
        limits = example_transfer.get_transfer_limits()
        db.session.delete(example_transfer)
        if len(limits) == 0:
            return None
        else:
            # might want to do something different if there's more than one limit...
            return limits[0]

    @staticmethod
    def get_exchange_rate(user: User, from_token: Token):
        to_token = user.get_reserve_token()
        exchange = Exchange()
        return exchange.get_exchange_rate(from_token, to_token)

    @staticmethod
    def transfer_token(sender: User, recipient: User, amount: float, reason_id: Optional[int] = None):
        sent_token = default_token(sender)
        received_token = default_token(recipient)

        transfer_use = None
        if reason_id is not None:
            transfer_use = str(int(reason_id))
        transfer = make_payment_transfer(amount, token=sent_token, send_user=sender, receive_user=recipient,
                                         transfer_use=transfer_use, is_ghost_transfer=True,
                                         require_sender_approved=False, require_recipient_approved=False)
        exchanged_amount = None

        if sent_token.id != received_token.id:
            exchange = Exchange()
            exchange.exchange_from_amount(user=recipient, from_token=sent_token, to_token=received_token,
                                          from_amount=amount, dependent_task_ids=[transfer.blockchain_task_id])
            exchanged_amount = exchange.to_transfer.transfer_amount

        return exchanged_amount

    @staticmethod
    def send_balance_sms(user: User):
        def get_token_info(transfer_account: TransferAccount):
            token = transfer_account.token
            limit = TokenProcessor.get_limit(user, token)
            exchange_rate = TokenProcessor.get_exchange_rate(user, token)
            return {
                "name": token.symbol,
                "balance": TokenProcessor.balance_for_transfer_account(transfer_account),
                "limit": limit,
                "exchange_rate": str(round(exchange_rate, 2))
            }

        def filter_incorrect_limit(token_info):
            return token_info['limit'] is not None and token_info['limit'].transfer_balance_percentage is not None

        reserve_token = user.get_reserve_token()
        # transfer accounts could be created for other currencies exchanged with, but we don't want to list those
        transfer_accounts = filter(lambda x: x.is_ghost is not True, user.transfer_accounts)
        token_info = list(map(get_token_info, transfer_accounts))
        token_balances = "\n".join(map(lambda x: f"{x['name']} {str(round(x['balance'], 2))}", token_info))
        exchangeable_tokens = filter(filter_incorrect_limit, token_info)
        token_exchanges = "\n".join(map(lambda x: f"{str(round(x['limit'].transfer_balance_percentage * x['balance'], 2))} {x['name']} (1 {x['name']} = {x['exchange_rate']} {reserve_token.symbol})", exchangeable_tokens))
        exchange_period = TokenProcessor.get_limit(user, default_token(user)).time_period_days

        TokenProcessor.send_sms(user, "send_balance_sms", token_balances=token_balances,
                                token_exchanges=token_exchanges, limit_period=exchange_period)

    @staticmethod
    def fetch_exchange_rate(user: User):
        from_token = default_token(user)

        limit = TokenProcessor.get_limit(user, from_token)
        if limit is not None and limit.transfer_balance_percentage is not None:
            exchange_limit = str(round(limit.transfer_balance_percentage * TokenProcessor.get_balance(user), 2))
            exchange_rate = TokenProcessor.get_exchange_rate(user, from_token)

            TokenProcessor.send_sms(user, "exchange_rate_sms", token_name=from_token.symbol,
                                    exchange_rate=str(round(exchange_rate, 2)), exchange_limit=exchange_limit,
                                    exchange_sample_value=str(round(exchange_rate * float(1000), 2)),
                                    limit_period=limit.time_period_days)

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        try:
            exchanged_amount = TokenProcessor.transfer_token(sender, recipient, amount, reason_id)

            tx_time = datetime.datetime.now()
            sender_balance = TokenProcessor.get_balance(sender)
            recipient_balance = TokenProcessor.get_balance(recipient)
            if exchanged_amount is None:
                TokenProcessor.send_success_sms("send_token_sender_sms", amount, sender, recipient, reason_str, tx_time,
                                                sender_balance)
                TokenProcessor.send_success_sms("send_token_recipient_sms", amount, recipient, sender, reason_str,
                                                tx_time, recipient_balance)
            else:
                TokenProcessor.exchange_success_sms("exchange_token_sender_sms", sender, recipient, amount,
                                                    exchanged_amount, tx_time, sender_balance)
                TokenProcessor.exchange_success_sms("exchange_token_agent_sms", recipient, sender, exchanged_amount,
                                                    amount, tx_time, recipient_balance)
        except Exception as e:
            TokenProcessor.send_sms(sender, "send_token_error_sms", amount=amount,
                                    token_name=default_token(sender).name, recipient=recipient.user_details())
            raise e

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        example_transfer = CreditTransfer(transfer_type='EXCHANGE', sender_user=sender, recipient_user=sender,
                                          token=default_token(sender), amount=amount)
        try:
            example_transfer.check_sender_transfer_limits()
            db.session.delete(example_transfer)

            # TODO: do agents have default token being reserve?
            to_amount = TokenProcessor.transfer_token(sender, agent, amount)
            tx_time = datetime.datetime.now()
            sender_balance = TokenProcessor.get_balance(sender)
            agent_balance = TokenProcessor.get_balance(agent)
            TokenProcessor.exchange_success_sms("exchange_token_sender_sms", sender, agent, amount, to_amount, tx_time,
                                                sender_balance)
            TokenProcessor.exchange_success_sms("exchange_token_agent_sms", agent, sender, to_amount, amount, tx_time,
                                                agent_balance)

        except TransactionPercentLimitError as e:
            TokenProcessor.send_sms(sender, "exchange_amount_error_sms", limit=f"{e.transfer_balance_percent * 100}%")
        except TransactionCountLimitError as e:
            TokenProcessor.send_sms(sender, "exchange_count_error_sms", transaction_count=e.transfer_count,
                                    limit_period=e.time_period_days)
