import datetime
from typing import Optional

from server import message_processor
from server.models.exchange import Exchange
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
        # TODO: convert amount?
        TokenProcessor.send_sms(message_key, amount=amount, token_name=default_token(user),
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'), reason=reason,
                                time=tx_time.strftime('%I:%M %p'), balance=balance)

    @staticmethod
    def exchange_success_sms(message_key: str, user: User, other_user: User, own_amount: float, other_amount: float,
                             tx_time: datetime, balance: float):
        # TODO: convert amounts?
        TokenProcessor.send_sms(message_key, own_amount=own_amount, other_amount=other_amount,
                                own_token_name=default_token(user), other_token_name=default_token(other_user),
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'),
                                time=tx_time.strftime('%I:%M %p'), balance=balance)

    @staticmethod
    def get_balance(user: User):
        return default_transfer_account(user).balance

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
        balance = TokenProcessor.get_balance(user)
        # TODO: send sms

    @staticmethod
    def fetch_exchange_rate(user: User):
        from_token = default_token(user)
        to_token = user.get_reserve_token()
        exchange = Exchange()
        exchange.get_exchange_rate(from_token, to_token)
        # TODO: send sms

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        TokenProcessor.transfer_token(sender, recipient, amount, reason_id)

        # TODO: failure sms

        tx_time = datetime.datetime.now()
        sender_balance = TokenProcessor.get_balance(sender)
        recipient_balance = TokenProcessor.get_balance(recipient)
        TokenProcessor.send_success_sms("send_token_sender_sms", amount, sender, recipient, reason_str, tx_time,
                                        sender_balance)
        TokenProcessor.send_success_sms("send_token_recipient_sms", amount, recipient, sender, reason_str, tx_time,
                                        recipient_balance)

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        # TODO: check limits - set transfer type as "EXCHANGE", catch AccountLimitError and send different sms
        # TODO: do agents have default token being reserve?
        to_amount = TokenProcessor.transfer_token(sender, agent, amount)

        # TODO: failure sms

        tx_time = datetime.datetime.now()
        sender_balance = TokenProcessor.get_balance(sender)
        agent_balance = TokenProcessor.get_balance(agent)
        TokenProcessor.exchange_success_sms("exchange_token_sender_sms", sender, agent, amount, to_amount, tx_time,
                                            sender_balance)
        TokenProcessor.exchange_success_sms("exchange_token_agent_sms", agent, sender, to_amount, amount, tx_time,
                                            agent_balance)

