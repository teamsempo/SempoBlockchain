import datetime
import pendulum
from typing import Optional, Tuple, Type
from sqlalchemy.sql import func

from server import db
from server.sempo_types import TransferAmount
from server.exceptions import (
    NoTransferAllowedLimitError,
    TransferBalanceFractionLimitError,
    MaximumPerTransferLimitError,
    TransferCountLimitError,
    TransferAmountLimitError,
    InsufficientBalanceError,
    MinimumSentLimitError
)
from server.models.credit_transfer import CreditTransfer
from server.models.exchange import Exchange
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.models.user import User

from server.utils.phone import send_message
from server.utils.misc import round_to_decimals, rounded_dollars, round_to_sig_figs
from server.utils.credit_transfer import make_payment_transfer
from server.models.utils import ephemeral_alchemy_object
from server.utils.internationalization import i18n_for
from server.utils.user import default_token, default_transfer_account
from server.utils.credit_transfer import cents_to_dollars
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferModeEnum
from server.utils.transfer_limits.limits import (
    AggregateTransferAmountMixin,
    AggregateLimit,
    BalanceFractionLimit,
    TotalAmountLimit
)

class TokenProcessor(object):


    @staticmethod
    def send_sms(user, message_key, **kwargs):
        # if we use token processor similarly for other countries later, can generalize country to init
        message = i18n_for(user, "ussd.kenya.{}".format(message_key), **kwargs)
        send_message(user.phone, message)

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
    def get_default_limit(user: User, token: Token) -> Optional[Tuple[AggregateLimit, TransferAmount]]:
        """
        :param user:
        :param token:
        :return: lowest amount limit applicable for a given CreditTransfer
        """

        with ephemeral_alchemy_object(
            CreditTransfer,
            transfer_type=TransferTypeEnum.PAYMENT,
            transfer_subtype=TransferSubTypeEnum.AGENT_OUT,
            sender_user=user,
            recipient_user=user,
            token=token,
            amount=0
        ) as dummy_transfer:

            limits = dummy_transfer.get_transfer_limits()

            if len(limits) == 0:
                return None

            amount_limits = filter(lambda l: isinstance(l, AggregateTransferAmountMixin), limits)
            with_amounts = [(limit, limit.available(dummy_transfer)) for limit in amount_limits]
            sorted_amount_limits = sorted(with_amounts, key=lambda l: l[1])
            return sorted_amount_limits[0] if len(sorted_amount_limits) > 0 else None

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
                                         transfer_subtype=transfer_subtype, transfer_mode=TransferModeEnum.USSD)
        exchanged_amount = None

        if sent_token.id != received_token.id:
            exchange = Exchange()
            exchange.exchange_from_amount(user=recipient, from_token=sent_token, to_token=received_token,
                                          from_amount=amount, prior_task_uuids=[transfer.blockchain_task_uuid],
                                          transfer_mode=TransferModeEnum.USSD)
            exchanged_amount = exchange.to_transfer.transfer_amount

        return exchanged_amount

    @staticmethod
    def send_balance_sms(user: User):

        token_balances_dollars, token_exchanges = TokenProcessor._get_token_balances(user)

        if token_exchanges in ["\n", '']:
            TokenProcessor.send_sms(
                user,
                "send_balance_sms",
                token_balances=token_balances_dollars)
            return

        default_limit, limit_amount = TokenProcessor.get_default_limit(user, default_token(user))
        if default_limit:
            TokenProcessor.send_sms(
                user,
                "send_balance_exchange_limit_sms",
                token_balances=token_balances_dollars,
                token_exchanges=token_exchanges,
                limit_period=default_limit.time_period_days)
            return

        TokenProcessor.send_sms(
            user,
            "send_balance_exchange_sms",
            token_balances=token_balances_dollars,
            token_exchanges=token_exchanges
        )

    @staticmethod
    def fetch_exchange_rate(user: User):
        from_token = default_token(user)

        default_limit, limit_amount = TokenProcessor.get_default_limit(user, from_token)
        exchange_rate_full_precision = TokenProcessor.get_exchange_rate(user, from_token)

        exchange_limit = rounded_dollars(limit_amount)
        exchange_rate = round_to_sig_figs(exchange_rate_full_precision, 3)
        exchange_sample_value = round(exchange_rate_full_precision * float(1000))

        if exchange_limit:
            TokenProcessor.send_sms(
                user,
                "exchange_rate_can_exchange_sms",
                token_name=from_token.symbol,
                exchange_rate=exchange_rate,
                exchange_limit=exchange_limit,
                exchange_sample_value=exchange_sample_value,
                limit_period=default_limit.time_period_days
            )
        else:
            TokenProcessor.send_sms(
                user,
                "exchange_rate_sms",
                token_name=from_token.symbol,
                exchange_rate=exchange_rate,
                exchange_sample_value=exchange_sample_value,
            )

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        try:
            exchanged_amount = TokenProcessor.transfer_token(sender, recipient, amount, reason_id)

            sender_tx_time = pendulum.now(sender.default_organisation.timezone)
            recipient_tx_time = pendulum.now(recipient.default_organisation.timezone)

            sender_balance = TokenProcessor.get_balance(sender)
            recipient_balance = TokenProcessor.get_balance(recipient)
            if exchanged_amount is None:
                TokenProcessor.send_success_sms(
                    "send_token_sender_sms",
                    sender, recipient, amount,
                    reason_str, sender_tx_time,
                    sender_balance)

                TokenProcessor.send_success_sms(
                    "send_token_recipient_sms",
                    recipient, sender, amount,
                    reason_str, recipient_tx_time,
                    recipient_balance)
            else:
                TokenProcessor.exchange_success_sms(
                    "exchange_token_sender_sms",
                    sender, recipient,
                    amount, exchanged_amount,
                    sender_tx_time, sender_balance)

                TokenProcessor.exchange_success_sms(
                    "exchange_token_agent_sms",
                    recipient, sender,
                    exchanged_amount,
                    amount, recipient_tx_time,
                    recipient_balance)

        except InsufficientBalanceError as e:
            token_balances_dollars, token_exchanges = TokenProcessor._get_token_balances(sender)

            TokenProcessor.send_sms(
                sender,
                "insufficient_balance_sms",
                amount=cents_to_dollars(amount),
                token_name=default_token(sender).name,
                recipient=recipient.user_details(),
                token_balances=token_balances_dollars
            )

        except TransferAmountLimitError as e:
            # Use a different message here from that used for exchange,
            # because the issue is caused by KYC (ie something the user can change by providing), rather than
            # our price-stability controls
            TokenProcessor.send_sms(
                sender,
                "transfer_amount_error_sms",
                amount=rounded_dollars(e.transfer_amount_limit),
                token=e.token,
                limit_period=e.limit_time_period_days
            )

        except Exception as e:
            # TODO: SLAP? all the others take input in cents
            TokenProcessor.send_sms(sender, "send_token_error_sms", amount=cents_to_dollars(amount),
                                    token_name=default_token(sender).name, recipient=recipient.user_details())

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        try:
            # TODO: do agents have default token being reserve?
            to_amount = TokenProcessor.transfer_token(
                sender, agent, amount, transfer_subtype=TransferSubTypeEnum.AGENT_OUT
            )
            sender_tx_time = pendulum.now(sender.default_organisation.timezone)
            agent_tx_time = pendulum.now(agent.default_organisation.timezone)
            sender_balance = TokenProcessor.get_balance(sender)
            agent_balance = TokenProcessor.get_balance(agent)
            TokenProcessor.exchange_success_sms(
                "exchange_token_sender_sms", sender, agent, amount, to_amount, sender_tx_time, sender_balance
            )
            TokenProcessor.exchange_success_sms(
                "exchange_token_agent_sms", agent, sender, to_amount, amount, agent_tx_time, agent_balance
            )

        except NoTransferAllowedLimitError as e:
            TokenProcessor.send_sms(
                sender,
                "exchange_not_allowed_error_sms",
            )

        except (TransferAmountLimitError, MinimumSentLimitError) as e:
            TokenProcessor.send_sms(
                sender,
                "exchange_amount_error_sms",
                amount=rounded_dollars(e.transfer_amount_limit),
                token=e.token,
                limit_period=e.limit_time_period_days
            )
        except TransferBalanceFractionLimitError as e:
            TokenProcessor.send_sms(
                sender,
                "exchange_fraction_error_sms",
                token=e.token,
                percent=f"{int(e.transfer_balance_fraction_limit * 100)}%"
            )
        except TransferCountLimitError as e:
            TokenProcessor.send_sms(
                sender,
                "exchange_count_error_sms",
                count=e.transfer_count_limit,
                token=e.token,
                limit_period=e.limit_time_period_days
            )
        except MaximumPerTransferLimitError as e:
            TokenProcessor.send_sms(
                sender,
                "maximum_per_transaction_error_sms",
                token=e.token,
                amount=e.maximum_amount_limit
            )

    @staticmethod
    def _get_token_balances(user: User):

        def get_token_info(transfer_account: TransferAccount):
            token = transfer_account.token
            limit, limit_amount = TokenProcessor.get_default_limit(user, token)
            exchange_rate = TokenProcessor.get_exchange_rate(user, token)
            return {
                "name": token.symbol,
                "balance": transfer_account.balance,
                "exchange_rate": exchange_rate,
                "limit": limit,
                "token": token
            }

        def check_if_ge_limit(token_info):
            return 'GE Liquid Token' in token_info['limit'].name

        def token_string(limit_type: Type[AggregateLimit], t: dict):
            if isinstance(t['limit'], limit_type):

                with ephemeral_alchemy_object(
                        CreditTransfer,
                        transfer_type=TransferTypeEnum.PAYMENT,
                        transfer_subtype=TransferSubTypeEnum.AGENT_OUT,
                        sender_user=user,
                        recipient_user=user,
                        token=t['token'],
                        amount=0
                ) as dummy_transfer:

                    allowed_amount = f"{rounded_dollars(str(t['limit'].available_base(dummy_transfer)))}"
                    rounded_rate = round_to_sig_figs(t['exchange_rate'], 3)
                    return (
                        f"{allowed_amount} {t['name']} (1 {t['name']} = {rounded_rate} {reserve_token.symbol})"
                    )
            else:
                return ""

            # transfer accounts could be created for other currencies exchanged with, but we don't want to list those

        transfer_accounts = filter(lambda x: x.is_ghost is not True, user.transfer_accounts)
        token_info_list = list(map(get_token_info, transfer_accounts))

        token_balances_dollars = "\n".join(map(lambda x: f"{x['name']} {rounded_dollars(x['balance'])}",
                                               token_info_list))

        reserve_token = user.get_reserve_token()
        ge_tokens = list(filter(check_if_ge_limit, token_info_list))
        is_ge = len(ge_tokens) > 0
        if is_ge:
            exchange_list = list(map(lambda i: token_string(BalanceFractionLimit, i), ge_tokens))
        else:
            exchange_list = list(map(lambda i: token_string(TotalAmountLimit, i), token_info_list))

        if len(exchange_list) == 0:
            token_exchanges = None
        else:
            token_exchanges = "\n".join(exchange_list)

        return token_balances_dollars, token_exchanges
