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
from server.models.utils import ModelBase


class TransferUsage(ModelBase):
    __tablename__ = 'transfer_usage'

    _name = db.Column(db.String, unique=True)
    is_cashout = db.Column(db.Boolean)
    _icon = db.Column(db.String)
    priority = db.Column(db.Integer)
    translations = db.Column(JSON)
    default = db.Column(db.Boolean)

    user = db.relationship(
        'User', backref='transfer_usage', lazy=True, uselist=False)

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
        stripped_name = name.strip()
        exists = db.session.query(TransferUsage.id).filter(
            func.lower(TransferUsage.name) == func.lower(stripped_name)).scalar() is not None
        if not exists:
            self._name = stripped_name
        else:
            raise TransferUsageNameDuplicateException(
                'Transfer usage name {} is duplicate'.format(name))
