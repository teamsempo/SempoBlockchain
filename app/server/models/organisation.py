from flask import current_app

from server import db
from server.utils.blockchain_tasks import (
    create_blockchain_wallet
)
from server.models.utils import ModelBase, organisation_association_table
from server import message_processor
from server.utils.i18n import i18n_for


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

    org_level_transfer_account_id    = db.Column(db.Integer, db.ForeignKey('transfer_account.id', name="fk_org_level_account"))
    # We use this weird join pattern because SQLAlchemy
    # doesn't play nice when doing multiple joins of the same table over different declerative bases
    org_level_transfer_account       = db.relationship("TransferAccount",
                                                       post_update=True,
                                                       primaryjoin="Organisation.org_level_transfer_account_id==TransferAccount.id",
                                                       uselist=False)

    credit_transfers    = db.relationship(
        "CreditTransfer",
        secondary=organisation_association_table,
        back_populates="organisations")

    transfer_accounts   = db.relationship('TransferAccount',
                                          backref='organisation',
                                          lazy=True, foreign_keys='TransferAccount.organisation_id')

    blockchain_addresses = db.relationship('BlockchainAddress', backref='organisation',
                                           lazy=True, foreign_keys='BlockchainAddress.organisation_id')

    email_whitelists    = db.relationship('EmailWhitelist', backref='organisation',
                                          lazy=True, foreign_keys='EmailWhitelist.organisation_id')

    custom_welcome_message_key = db.Column(db.String)


    def __init__(self, **kwargs):
        super(Organisation, self).__init__(**kwargs)

        self.system_blockchain_address = create_blockchain_wallet(
            wei_target_balance=current_app.config['SYSTEM_WALLET_TARGET_BALANCE'],
            wei_topup_threshold=current_app.config['SYSTEM_WALLET_TOPUP_THRESHOLD'],
        )

    def send_welcome_sms(self, to_user):
        if self.custom_welcome_message_key:
            message = i18n_for(to_user, "organisation.{}".format(self.custom_welcome_message_key))
        else:
            message = i18n_for(to_user, "organisation.generic_welcome_message")
        message_processor.send_message(to_user.phone, message)
