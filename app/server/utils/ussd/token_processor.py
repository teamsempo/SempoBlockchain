import datetime
from typing import Optional

from server import message_processor
from server.exceptions import TransactionPercentLimitError, TransactionCountLimitError
from server.models.credit_transfer import CreditTransfer
from server.models.exchange import Exchange
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.utils.credit_transfer import make_payment_transfer
from server.utils.i18n import i18n_for
from server.models.user import User
from server.utils.user import default_token, default_transfer_account


class TokenProcessor(object):
    @staticmethod
    def send_sms(user, message_key, **kwargs):
        # if we use token processor similarly for other countries later, can generalize country to init
        message = i18n_for(user, "ussd.kenya.{}".format(message_key), **kwargs)
        message_processor.send_message(user.phone, message)

    @staticmethod
    def send_success_sms(message_key: str, amount: float, user: User, other_user: User, reason: str, tx_time: datetime,
                         balance: float):
        # TODO: convert amounts - truncate? need to turn from cents to dollar?
        TokenProcessor.send_sms(user, message_key, amount=amount, token_name=default_token(user),
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'), reason=reason,
                                time=tx_time.strftime('%I:%M %p'), balance=balance)

    @staticmethod
    def exchange_success_sms(message_key: str, user: User, other_user: User, own_amount: float, other_amount: float,
                             tx_time: datetime, balance: float):
        # TODO: convert amounts - truncate? need to turn from cents to dollar?
        TokenProcessor.send_sms(user, message_key, own_amount=own_amount, other_amount=other_amount,
                                own_token_name=default_token(user), other_token_name=default_token(other_user),
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'),
                                time=tx_time.strftime('%I:%M %p'), balance=balance)

    @staticmethod
    def get_balance(user: User):
        return default_transfer_account(user).balance

    @staticmethod
    def get_limit(user: User, token: Token):
        example_transfer = CreditTransfer(transfer_type='EXCHANGE', sender_user=user, token=token, amount=0)
        limits = example_transfer.get_transfer_limits()
        if len(limits) != 1:
            raise Exception("Unexpected limit count for user {} exchanging {}".format(user.id, token.name))
        else:
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

        transfer = make_payment_transfer(amount, token=sent_token, send_user=sender, receive_user=recipient,
                                         transfer_use=reason_id)
        received_amount = amount

        if sent_token.id != received_token.id:
            exchange = Exchange()
            exchange.exchange_from_amount(user=recipient, from_token=sent_token, to_token=received_token,
                                          from_amount=amount, dependent_task_ids=[transfer.blockchain_task_id])
            received_amount = exchange.to_transfer.to_amount

        return received_amount

    @staticmethod
    def send_balance_sms(user: User):
        def get_token_info(transfer_account: TransferAccount):
            token = transfer_account.token
            limit = TokenProcessor.get_limit(user, token)
            return {
                # TODO: is it name or symbol?
                "name": token.name,
                "balance": transfer_account.balance,
                "limit": limit.transfer_balance_percentage,
                "exchange_rate": TokenProcessor.get_exchange_rate(user, token)
            }
        # TODO: should we merge transfer accounts with same tokens..? any currencies we should filter out?
        token_info = map(get_token_info, user.transfer_accounts)
        token_balances = "\n".join(map(lambda x: f"{x['name']} {x['balance']}", token_info))
        # this one is also not well generalized currently - how get real world currency name of reserve token?
        token_exchanges = "\n".join(
            map(lambda x: f"{x['limit'] * x['balance']} {x['name']} (1 {x['name']} = {x['exchange_rate']} KSH)",
                token_info))

        TokenProcessor.send_sms(user, "send_balance_sms", token_balances=token_balances,
                                token_exchanges=token_exchanges)

    @staticmethod
    def fetch_exchange_rate(user: User):
        from_token = default_token(user)

        limit = TokenProcessor.get_limit(user, from_token)
        exchange_limit = limit.transfer_balance_percentage * default_transfer_account(user).balance
        exchange_rate = TokenProcessor.get_exchange_rate(user, from_token)

        TokenProcessor.send_sms(user, "exchange_rate_sms", token_name=from_token.name, exchange_rate=exchange_rate,
                                exchange_sample_value={exchange_rate * float(1000)}, exchange_limit={exchange_limit},
                                limit_period={limit.time_period_days})

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        try:
            TokenProcessor.transfer_token(sender, recipient, amount, reason_id)

            tx_time = datetime.datetime.now()
            sender_balance = TokenProcessor.get_balance(sender)
            recipient_balance = TokenProcessor.get_balance(recipient)
            TokenProcessor.send_success_sms("send_token_sender_sms", amount, sender, recipient, reason_str, tx_time,
                                            sender_balance)
            TokenProcessor.send_success_sms("send_token_recipient_sms", amount, recipient, sender, reason_str, tx_time,
                                            recipient_balance)
        except Exception:
            TokenProcessor.send_sms(sender, "send_token_error_sms", amount=amount,
                                    token_name=default_token(sender).name, recipient=recipient.user_details())

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        example_transfer = CreditTransfer(transfer_type='EXCHANGE', sender_user=sender, token=default_token(sender),
                                          amount=amount)
        try:
            example_transfer.check_sender_transfer_limits()

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
