from flask import current_app

from server import db, bt
from server.models.utils import ModelBase, organisation_association_table


class Organisation(ModelBase):
    """
    Establishes organisation object that resources can be associated with.
    """
    __tablename__       = 'organisation'

    name                = db.Column(db.String)

    system_blockchain_address = db.Column(db.String)

    users               = db.relationship(
        "User",
        secondary=organisation_association_table,
        back_populates="organisations")

    token_id            = db.Column(db.Integer, db.ForeignKey('token.id'))

    org_level_transfer_account_id    = db.Column(db.Integer,
                                                 db.ForeignKey('transfer_account.id',
                                                               name="fk_org_level_account"))

    # We use this weird join pattern because SQLAlchemy
    # doesn't play nice when doing multiple joins of the same table over different declerative bases
    org_level_transfer_account = db.relationship(
        "TransferAccount",
        post_update=True,
        primaryjoin="Organisation.org_level_transfer_account_id==TransferAccount.id",
        uselist=False)

    credit_transfers    = db.relationship("CreditTransfer",
                                          secondary=organisation_association_table,
                                          back_populates="organisations")

    transfer_accounts   = db.relationship('TransferAccount',
                                          backref='organisation',
                                          lazy=True, foreign_keys='TransferAccount.organisation_id')

    blockchain_addresses = db.relationship('BlockchainAddress', backref='organisation',
                                           lazy=True, foreign_keys='BlockchainAddress.organisation_id')

    email_whitelists    = db.relationship('EmailWhitelist', backref='organisation',
                                          lazy=True, foreign_keys='EmailWhitelist.organisation_id')


    def __init__(self, **kwargs):
        super(Organisation, self).__init__(**kwargs)

        self.system_blockchain_address = bt.create_blockchain_wallet(
            wei_target_balance=current_app.config['SYSTEM_WALLET_TARGET_BALANCE'],
            wei_topup_threshold=current_app.config['SYSTEM_WALLET_TOPUP_THRESHOLD'],
        )
