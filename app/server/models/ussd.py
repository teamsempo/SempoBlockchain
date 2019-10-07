from sqlalchemy.dialects.postgresql import JSON

from server import db
from server.models.utils import ModelBase

class UssdMenu(ModelBase):
    __tablename__ = 'ussd_menus'

    name = db.Column(db.String, nullable=False, index=True, unique=True)
    description = db.Column(db.String)
    parent_id = db.Column(db.Integer)
    """
        TODO: change how we do i18n
        keeping this as is from migration from grassroots economics
        but this system is really bad since we always need 
        all languages defined for all new menu items, no graceful fallback 
    """
    display_text_en = db.Column(db.String, nullable=False)
    display_text_sw = db.Column(db.String, nullable=False)

class UssdSession(ModelBase):
    __tablename__ = 'ussd_sessions'

    session_id = db.Column(db.String, nullable=False, index=True, unique=True)
    user_id = db.Column(db.Integer)
    service_code = db.Column(db.String, nullable=False)
    msisdn = db.Column(db.String, nullable=False)
    user_input = db.Column(db.String)
    ussd_menu_id = db.Column(db.Integer, nullable=False)
    state = db.Column(db.String, nullable=False)
    sessions_data = db.Column(JSON)

