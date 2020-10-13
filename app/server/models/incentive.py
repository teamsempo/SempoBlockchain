from server.models.utils import ModelBase
from sqlalchemy.dialects.postgresql import JSON
from server.models.organisation import Organisation
from server.models.credit_transfer import CreditTransfer
from server.utils.credit_transfer import make_payment_transfer
from server.utils.transfer_enums import TransferSubTypeEnum
from server.exceptions import IncetiveLimitExceeded

from server import db
from server import constants 

from datetime import date, timedelta
from sqlalchemy import func

class Incentive(ModelBase):
    """
    Incentives applied to transacitons at an orgnisation-level 
    The crux of this model is built on the incentive_rules schema described below:
    {
        'transfer_method': 'NFC',
        'incentive_type': 'PERCENTAGE',
        'incentive_amount': 100,
        'incentive_recipient': 'RECIPIENT',
        'restrictions': [
            {
                'style': 'transaction_count',
                'days': 7,
                'transactions': 5
            },
            {
                'style': 'currency',
                'days': 7,
                'limit': 5000
            }
        ],
    }

    transfer_method: Is the incentive targeting QR or NFC transactions
    incentive_types: Possible incentive types are PERCENTAGE or FIXED. 
        - PERCENTAGE - give incentive_recipient a set percentage of transactions
        - FIXED - give incentive_recipient a fixed amount of money for each transaction
    incentive_amount: amount or percentage of transaction to give incentive_recipient
    incentive_recipient: Possible values are RECIPIENT or SENDER
    restrictions: 
        - style: transaction_count
            - days: Rolling window of how many days this incentive can be triggered
            - transactions: number of transactions the sender user made in that window of days
        - style: currency
            - days: Rolling window of how many days this incentive can be triggered
            - limit: Total spent by the sender user (BEFORE the currently evaluated incentive is applied)
    """

    __tablename__       = 'incentive'
    incentive_rules = db.Column(JSON)
    organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))

    def handle_incentive(self, transfer, method, do_not_transact = False):
        """
        Handles incentives-- checks if they are applicable, then makes the insentive payment
        """
        # See if the insentive is relevant
        if self.incentive_rules['transfer_method'] != method or self.incentive_rules['transfer_method'] != 'ANY':
            return False

        # Get incentive amounts, calculate percentage if relevant
        if self.incentive_rules['incentive_type'] == 'FIXED':
            incentive_amount = self.incentive_rules['incentive_amount']
        elif self.incentive_rules['incentive_type'] == 'PERCENTAGE':
            incentive_amount = transfer.transfer_amount * float(self.incentive_rules['incentive_amount'] / 100)

        # Determine who gets the cash!
        if self.incentive_rules['incentive_recipient'] == 'SENDER':
            incentive_recipient_transfer_account = transfer.sender_transfer_account
            incentive_recipient_user = transfer.sender_user
        elif self.incentive_rules['incentive_recipient'] == 'RECIPIENT':
            incentive_recipient_transfer_account = transfer.recipient_transfer_account
            incentive_recipient_user = transfer.recipient_user

        # Process restrictions, apply them to sender_user
        for r in self.incentive_rules['restrictions']:
            time_diff = timedelta(days=r['days'])
            time_window_start = date.today() - time_diff
            if r['style'] == 'transaction_count':
                transaction_count = db.session.query(func.count(CreditTransfer.id))\
                        .filter(CreditTransfer.sender_transfer_account == transfer.sender_transfer_account)\
                        .filter(CreditTransfer.created > time_window_start)\
                        .scalar()
                if transaction_count > r['transactions']:
                    raise IncetiveLimitExceeded(f'Cannot invoke incentive {self.id}-- {transaction_count} of {r["transactions"]} transacitons have been completed in the past {r["days"]} days')
            
            elif r['style'] == 'currency':
                transaction_sum = db.session.query(func.sum(CreditTransfer.transfer_amount))\
                        .filter(CreditTransfer.sender_transfer_account == transfer.sender_transfer_account)\
                        .filter(CreditTransfer.created > time_window_start)\
                        .scalar()
                if transaction_sum > r['limit']:
                    raise IncetiveLimitExceeded(f'Cannot invoke incentive {self.id}-- {transaction_sum} of {r["limit"]} has been spent in the past {r["days"]} days')

        # None of the restrictions have been tripped, so let's make the transfer!
        if not do_not_transact:
            return make_payment_transfer(
                                    transfer_amount=incentive_amount,
                                    send_transfer_account=self.organisation.org_level_transfer_account,
                                    send_user=self.organisation.org_level_transfer_account.primary_user,
                                    receive_user=incentive_recipient_user,
                                    receive_transfer_account=incentive_recipient_transfer_account,
                                    transfer_subtype=TransferSubTypeEnum.FEE,
                                    require_sender_approved=False,
                                )
        else:
            return True 
    
    def __init__(self, **kwargs):
        super(Incentive, self).__init__(**kwargs)
        if 'transfer_method' not in self.incentive_rules:
            raise Exception ('No transfer_method provided')
        if 'incentive_type' not in self.incentive_rules:
            raise Exception ('No incentive_type provided')
        if 'incentive_recipient' not in self.incentive_rules:
            raise Exception ('No incentive_recipient provided')
        if 'incentive_amount' not in self.incentive_rules:
            raise Exception ('No incentive_amount provided')

        transfer_method = self.incentive_rules['transfer_method']
        incentive_type = self.incentive_rules['incentive_type']
        incentive_recipient = self.incentive_rules['incentive_recipient']
        incentive_amount = self.incentive_rules['incentive_amount']
        restrictions = self.incentive_rules['restrictions'] or []

        # Whole lotta validation!
        if transfer_method not in constants.INCENTIVE_TRANSFER_METHODS:
            raise Exception (f'{transfer_method} not a valid transfer method. Select one of {constants.INCENTIVE_TRANSFER_METHODS}')
        if incentive_type not in constants.INCENTIVE_TYPES:
            raise Exception (f'{incentive_type} not a valid transfer method. Select one of {constants.INCENTIVE_TYPES}')
        if incentive_recipient not in constants.INCENTIVE_RECIPIENTS:
            raise Exception (f'{incentive_recipient} not a valid transfer method. Select one of {constants.INCENTIVE_RECIPIENTS}')

        for r in self.incentive_rules['restrictions']:
            # Validate transaction_count 
            if r['style'] == 'transaction_count':
                if not r['days']:
                    raise Exception (f'transaction_count restriction requires \'days\' parameter')
                if not r['transactions'] and r['transactions'] != 0:
                    raise Exception (f'transaction_count restriction requires \'transactions\' parameter')
            # Validate currency 
            elif r['style'] == 'currency':
                if not r['days']:
                    raise Exception (f'currency restriction requires \'days\' parameter')
                if not r['limit'] and r['limit'] != 0:
                    raise Exception (f'currency restriction requires \'limit\' parameter')
            else:
                raise Exception (f'{r["style"]} not a valid restriction style. Please choose \'transaction_count\' or \'currency\'')
