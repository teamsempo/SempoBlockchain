from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from server.exceptions import (
    IconNotSupportedException,
    TransferUsageNameDuplicateException
)
from server.constants import (
    MATERIAL_COMMUNITY_ICONS
)

from server import db
from server.models.utils import ModelBase, credit_transfer_transfer_usage_association_table

class TransferUsage(ModelBase):
    __tablename__ = 'transfer_usage'

    _name = db.Column(db.String, unique=True)
    is_cashout = db.Column(db.Boolean)
    _icon = db.Column(db.String)
    priority = db.Column(db.Integer)
    translations = db.Column(JSON)
    default = db.Column(db.Boolean)

    users = db.relationship('User', backref='business_usage', lazy=True)

    credit_transfers = db.relationship(
        "CreditTransfer",
        secondary=credit_transfer_transfer_usage_association_table,
        back_populates="transfer_usages",
    )

    @hybrid_property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        if icon not in MATERIAL_COMMUNITY_ICONS:
            raise IconNotSupportedException(f'Icon {icon} not supported or found')
        self._icon = icon

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        stripped_name = name.strip()
        exists = db.session.query(TransferUsage.id).filter(
            func.lower(TransferUsage.name) == func.lower(stripped_name)).scalar() is not None
        if not exists:
            self._name = stripped_name
        else:
            raise TransferUsageNameDuplicateException(
                'Transfer usage name {} is duplicate'.format(name))

    @classmethod
    def find_or_create(cls, raw_name, default=False, **kwargs) -> "TransferUsage":
        name = raw_name.strip()
        usage = db.session.query(TransferUsage).filter(
            func.lower(TransferUsage.name) == func.lower(name)).first()
        if usage is None:
            usage = cls(name=name, default=default, **kwargs)
            db.session.add(usage)
        return usage

    def __repr__(self):
        return f'<Transfer Usage {self.id}: {self.name}>'