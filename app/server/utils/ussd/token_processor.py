import datetime
from typing import Optional
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.sql import func

from server import db, message_processor
from server.exceptions import TransactionPercentLimitError, TransactionCountLimitError
from server.models.credit_transfer import CreditTransfer
from server.models.exchange import Exchange
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.models.user import User

from server.utils.misc import round_amount, rounded_dollars
from server.utils.credit_transfer import make_payment_transfer
from server.utils.i18n import i18n_for
from server.utils.user import default_token, default_transfer_account
from server.utils.credit_transfer import cents_to_dollars
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum
from server.utils.transfer_limits import TransferLimit


class TokenProcessor(object):

    @staticmethod
    def send_sms(user, message_key, **kwargs):
        # if we use token processor similarly for other countries later, can generalize country to init
        message = i18n_for(user, "ussd.kenya.{}".format(message_key), **kwargs)
        message_processor.send_message(user.phone, message)

    @staticmethod
    def send_success_sms(message_key: str, user: User, other_user: User, amount: float, reason: str, tx_time: datetime,
                         balance: float):

        amount_dollars = rounded_dollars(amount)
        rounded_balance_dollars = rounded_dollars(balance)

        TokenProcessor.send_sms(user, message_key, amount=amount_dollars, token_name=default_token(user).symbol,
                                other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'), reason=reason,
                                time=tx_time.strftime('%I:%M %p'), balance=rounded_balance_dollars)

    @staticmethod
    def exchange_success_sms(message_key: str, user: User, other_user: User, own_amount: float, other_amount: float,
                             tx_time: datetime, balance: float):

        rounded_own_amount_dollars = rounded_dollars(own_amount)
        rounded_other_amount_dollars = rounded_dollars(other_amount)
        rounded_balance_dollars = rounded_dollars(balance)

        TokenProcessor.send_sms(
            user, message_key,
            own_amount=rounded_own_amount_dollars, other_amount=rounded_other_amount_dollars,
            own_token_name=default_token(user).symbol, other_token_name=default_token(other_user).symbol,
            other_user=other_user.user_details(), date=tx_time.strftime('%d/%m/%Y'),
            time=tx_time.strftime('%I:%M %p'), balance=rounded_balance_dollars)

    @staticmethod
    def get_balance(user: User):
        return default_transfer_account(user).balance

    @staticmethod
    def get_default_limit(user: User, token: Token, transfer_account: TransferAccount) -> Optional[TransferLimit]:
        """
        :param user:
        :param token:
        :param transfer_account:
        :return: lowest limit applicable for a given CreditTransfer
        """
        example_transfer = CreditTransfer(
            transfer_type=TransferTypeEnum.PAYMENT,
            transfer_subtype=TransferSubTypeEnum.AGENT_OUT,
            sender_user=user,
            recipient_user=user,
            token=token,
            amount=0)

        limits = example_transfer.get_transfer_limits()

        try:
            # Sometimes some weird db behaviour cause the above transfer to be persisted.
            # This is here to make sure it definitely doesn't hang around
            db.session.delete(example_transfer)
        except Exception as e:
            pass

        if len(limits) == 0:
            return None
        else:
            # should only ever be one ge limit
            ge_limit = [limit for limit in limits if 'GE Liquid Token' in limit.name]

            lowest_limit = None
            lowest_amount_avail = float('inf')

            for limit in limits:
                if 'GE Liquid Token' not in limit.name:
                    transaction_volume = limit.apply_all_filters(
                        example_transfer,
                        db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
                    ).execution_options(show_all=True).first().total

                    amount_avail = limit.total_amount - (transaction_volume or 0)
                    if amount_avail < (ge_limit[0].transfer_balance_fraction * transfer_account.balance)\
                            and amount_avail < lowest_amount_avail:
                        lowest_limit = limit
                        lowest_amount_avail = amount_avail

            if lowest_limit:
                return lowest_limit
            else:
                return ge_limit[0]

    @staticmethod
    def get_default_exchange_limit(limit: TransferLimit, user: Optional[User]):
        if limit is not None and limit.transfer_balance_fraction is not None:
            return round_amount(
                limit.transfer_balance_fraction * TokenProcessor.get_balance(user)
            )
        elif limit.total_amount is not None:
            return round_amount(
                limit.total_amount
            )
        else:
            return None

    @staticmethod
    def get_exchange_rate(user: User, from_token: Token):
        to_token = user.get_reserve_token()
        if from_token == to_token:
            return None
        exchange = Exchange()
        return exchange.get_exchange_rate(from_token, to_token)

    @staticmethod
    def transfer_token(sender: User,
                       recipient: User,
                       amount: float,
                       reason_id: Optional[int] = None,
                       transfer_subtype: Optional[TransferSubTypeEnum]=TransferSubTypeEnum.STANDARD):

        sent_token = default_token(sender)
        received_token = default_token(recipient)

        transfer_use = None
        if reason_id is not None:
            transfer_use = str(int(reason_id))
        transfer = make_payment_transfer(amount, token=sent_token, send_user=sender, receive_user=recipient,
                                         transfer_use=transfer_use, is_ghost_transfer=True,
                                         require_sender_approved=False, require_recipient_approved=False,
                                         transfer_subtype=transfer_subtype)
        exchanged_amount = None

        if sent_token.id != received_token.id:
            exchange = Exchange()
            exchange.exchange_from_amount(user=recipient, from_token=sent_token, to_token=received_token,
                                          from_amount=amount, dependent_task_uuids=[transfer.blockchain_task_uuid])
            exchanged_amount = exchange.to_transfer.transfer_amount

        return exchanged_amount

    @staticmethod
    def send_balance_sms(user: User):

        def get_token_info(transfer_account: TransferAccount):
            token = transfer_account.token
            limit = TokenProcessor.get_default_limit(user, token, transfer_account)
            exchange_rate = TokenProcessor.get_exchange_rate(user, token)
            return {
                "name": token.symbol,
                "balance": transfer_account.balance,
                "exchange_rate": exchange_rate,
                "limit": limit,
            }

        def check_if_ge_limit(token_info):
            # return 'GE Liquid Token' in token_info['limit'].name
            return (token_info['exchange_rate'] is not None
                    and token_info['limit'] is not None
                    and token_info['limit'].transfer_balance_fraction is not None)

        # transfer accounts could be created for other currencies exchanged with, but we don't want to list those
        transfer_accounts = filter(lambda x: x.is_ghost is not True, user.transfer_accounts)
        token_info_list = list(map(get_token_info, transfer_accounts))

        token_balances_dollars = "\n".join(map(lambda x: f"{x['name']} {rounded_dollars(x['balance'])}",
                                               token_info_list))

        reserve_token = user.get_reserve_token()
        ge_tokens = list(filter(check_if_ge_limit, token_info_list))
        is_ge = len(ge_tokens) > 0
        if is_ge:
            token_exchanges = "\n".join(
                map(lambda x: f"{rounded_dollars(x['limit'].transfer_balance_fraction * x['balance'])}"
                              f" {x['name']} (1 {x['name']} = {x['exchange_rate']} {reserve_token.symbol})",
                    ge_tokens))
        else:
            token_exchanges = "\n".join(
                map(lambda x: f"{rounded_dollars(str(x['limit'].total_amount))}"
                              f" {x['name']} (1 {x['name']} = {x['exchange_rate']} {reserve_token.symbol})",
                    token_info_list))

        default_limit = TokenProcessor.get_default_limit(user, default_token(user), default_transfer_account(user))
        if default_limit:
            TokenProcessor.send_sms(
                user,
                "send_balance_limit_sms",
                token_balances=token_balances_dollars,
                token_exchanges=token_exchanges,
                limit_period=default_limit.time_period_days)
        else:
            TokenProcessor.send_sms(
                user,
                "send_balance_sms",
                token_balances=token_balances_dollars,
                token_exchanges=token_exchanges
            )

    @staticmethod
    def fetch_exchange_rate(user: User):
        from_token = default_token(user)

        default_limit = TokenProcessor.get_default_limit(user, from_token, default_transfer_account(user))
        exchange_limit = TokenProcessor.get_default_exchange_limit(default_limit, user)
        exchange_rate = TokenProcessor.get_exchange_rate(user, from_token)

        TokenProcessor.send_sms(
            user,
            "exchange_rate_sms",
            token_name=from_token.symbol,
            exchange_rate=exchange_rate,
            exchange_limit=rounded_dollars(exchange_limit),
            exchange_sample_value=rounded_dollars(exchange_rate * float(1000)),
            limit_period=default_limit.time_period_days
        )

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        try:
            exchanged_amount = TokenProcessor.transfer_token(sender, recipient, amount, reason_id)

            tx_time = datetime.datetime.now()
            sender_balance = TokenProcessor.get_balance(sender)
            recipient_balance = TokenProcessor.get_balance(recipient)
            if exchanged_amount is None:
                TokenProcessor.send_success_sms(
                    "send_token_sender_sms",
                    sender, recipient, amount,
                    reason_str, tx_time,
                    sender_balance)

                TokenProcessor.send_success_sms(
                    "send_token_recipient_sms",
                    recipient, sender, amount,
                    reason_str, tx_time,
                    recipient_balance)
            else:
                TokenProcessor.exchange_success_sms(
                    "exchange_token_sender_sms",
                    sender, recipient,
                    amount, exchanged_amount,
                    tx_time, sender_balance)

                TokenProcessor.exchange_success_sms(
                    "exchange_token_agent_sms",
                    recipient, sender,
                    exchanged_amount,
                    amount, tx_time,
                    recipient_balance)

        except Exception as e:
            # TODO: SLAP? all the others take input in cents
            TokenProcessor.send_sms(sender, "send_token_error_sms", amount=cents_to_dollars(amount),
                                    token_name=default_token(sender).name, recipient=recipient.user_details())
            raise e

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        example_transfer = CreditTransfer(
            transfer_type=TransferTypeEnum.EXCHANGE,
            sender_user=sender,
            recipient_user=sender,
            token=default_token(sender),
            amount=amount)

        try:
            example_transfer.check_sender_transfer_limits()

            try:
                db.session.delete(example_transfer)
            except InvalidRequestError:
                # Instance is already deleted
                pass

            # TODO: do agents have default token being reserve?
            to_amount = TokenProcessor.transfer_token(
                sender, agent, amount, transfer_subtype=TransferSubTypeEnum.AGENT_OUT
            )
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
