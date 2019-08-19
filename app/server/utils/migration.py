from server.models import CreditTransfer

from datetime import datetime

def add_user_id_to_credit_transfer_column():

    credit_transfers = CreditTransfer.query.all()

    for credit_transfer in credit_transfers:

        if (credit_transfer.sender_user is None) and credit_transfer.sender_transfer_account:
            credit_transfer.sender_user = credit_transfer.sender_transfer_account.primary_user

        if (credit_transfer.recipient_user is None) and credit_transfer.recipient_transfer_account:
            credit_transfer.recipient_user = credit_transfer.recipient_transfer_account.primary_user
