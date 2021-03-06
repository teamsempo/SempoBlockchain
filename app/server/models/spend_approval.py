from server import db, bt
from server.models.utils import ModelBase

class SpendApproval(ModelBase):
    __tablename__ = 'spend_approval'

    eth_send_task_uuid = db.Column(db.String)
    approval_task_uuid = db.Column(db.String)
    receiving_address = db.Column(db.String)

    token_id                      = db.Column(db.Integer, db.ForeignKey("token.id"))
    giving_transfer_account_id    = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))

    def __init__(self, transfer_account_giving_approval, address_getting_approved):
        self.giving_transfer_account = transfer_account_giving_approval

        self.token = transfer_account_giving_approval.token

        self.receiving_address = address_getting_approved

        eth_send_task_uuid = bt.send_eth(
            signing_address=transfer_account_giving_approval.organisation.system_blockchain_address,
            recipient_address=transfer_account_giving_approval.blockchain_address,
            amount_wei=0.00184196 * 10**18)

        approval_task_uuid = bt.make_approval(
            signing_address=transfer_account_giving_approval.blockchain_address,
            token=self.token,
            spender=address_getting_approved,
            amount=1000000,
            prior_tasks=[eth_send_task_uuid])

        self.eth_send_task_uuid = eth_send_task_uuid
        self.approval_task_uuid = approval_task_uuid
