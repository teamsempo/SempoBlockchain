import os
import sys

from datetime import datetime
from datetime import timedelta
from app.server.utils.credit_transfer import make_payment_transfer
from app.server.utils.transfer_enums import TransferSubTypeEnum

app_directory = os.path.abspath(os.path.join(os.getcwd(), "../../app"))
sys.path.append(app_directory)
sys.path.append(os.getcwd())

from app.server import  db
from app.server.models.user import User


def total_unique_outward_transactions_per_user_sets():
    """"
    This method queries the database for all unique outward transactions for each user and returns a list of tuples
    with a user id, their blockchain address and their total unique outward transactions.
    [(user_id, blockchain_address, total_unique_outward_transactions)]
    SEARCH CRITERIA
        - count unique recipient user id.
        - transfer amount is greater or equal to 20.
        - credit transfers add since 24hrs ago.
        - credit transfer status is COMPLETE
        - transfer subtype STANDARD
    """
    sql_query = '''SELECT
    credit_transfer.sender_user_id,
    transfer_account.blockchain_address,
    COUNT (DISTINCT (credit_transfer.recipient_user_id))
    FROM credit_transfer
    LEFT JOIN transfer_account 
    ON credit_transfer.sender_transfer_account_id = transfer_account .id
    WHERE credit_transfer._transfer_amount_wei >= (2*10e17)
    AND credit_transfer.created > '{}'
    AND credit_transfer.transfer_status = 'COMPLETE'
    AND credit_transfer.transfer_subtype = 'STANDARD'
    GROUP BY 
    credit_transfer.sender_user_id,
    transfer_account.blockchain_address;'''.format((datetime.now() - timedelta(hours=24)))

    result = db.session.execute(sql_query)
    unique_transaction_sets = result.fetchall()

    return unique_transaction_sets


# define sets with total unique transactions per user
UNIQUE_TRANSACTION_SETS = total_unique_outward_transactions_per_user_sets()


def total_user_unique_outward_transactions():
    # compute total unique outward transactions for each user
    total_unique_outward_transactions = 0
    for counter, (user_id,
                  blockchain_address,
                  unique_outward_transactions_per_user) in enumerate(UNIQUE_TRANSACTION_SETS):
        total_unique_outward_transactions += unique_outward_transactions_per_user

    return total_unique_outward_transactions


class BonusProcessor:
    """
    This class is responsible for processing different bonus issuance and pre-scheduled incentive
    disbursements.
    """

    def __init__(self, issuable_amount):
        self.issuable_amount = issuable_amount

    def auto_disburse_daily_bonus(self):
        total_outward_transactions = total_user_unique_outward_transactions()

        for counter, (user_id,
                      blockchain_address,
                      unique_outward_transactions_per_user) in enumerate(UNIQUE_TRANSACTION_SETS):

            # compute percentage as per user
            user_percentage_unique_outward_transactions = (
                (unique_outward_transactions_per_user/total_outward_transactions))

            print('UNIQUE_TX_PER_USR: {}. TOTAL_OUTWARD_TX: {}. USR_PERCENTAGE_TX: {}.'
                  .format(unique_outward_transactions_per_user,
                          total_outward_transactions,
                          user_percentage_unique_outward_transactions))

            bonus_amount = user_percentage_unique_outward_transactions * self.issuable_amount

            # TODO [Philip]: Find a way to avoid this query
            user = User.query.filter_by(id=user_id).first()

            if bonus_amount > 1 and user:
                disbursement = make_payment_transfer(bonus_amount,
                                                     receive_user=user,
                                                     transfer_subtype=TransferSubTypeEnum.DISBURSEMENT)
                return disbursement
