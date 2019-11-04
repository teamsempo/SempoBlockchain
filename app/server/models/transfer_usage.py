from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property
from server.exceptions import (
    IconNotSupportedException
)
from server.constants import (
    MATERIAL_COMMUNITY_ICONS
)

from server import db
from server.models.utils import ModelBase


class TransferUsage(ModelBase):
    __tablename__ = 'transfer_usage'

    _name = db.Column(db.String, unique=True)
    is_cashout = db.Column(db.Boolean)
    _icon = db.Column(db.String)
    priority = db.Column(db.Integer)
    translations = db.Column(JSON)
    default = db.Column(db.Boolean)

    @hybrid_property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        if icon not in MATERIAL_COMMUNITY_ICONS:
            raise IconNotSupportedException('Icon {} not supported or found')
        self._icon = icon

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name.strip().upper()

    @classmethod
    def find_or_create(cls, raw_name, default=False) -> "TransferUsage":
        name = raw_name.strip().upper()
        usage = TransferUsage.query.filter_by(
            name=name).first()
        if usage is None:
            usage = cls(name=name, default=default)
            db.session.add(usage)
            db.session.commit()
        return usage
