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

    name = db.Column(db.String)
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
