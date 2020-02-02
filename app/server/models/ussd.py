from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
import sentry_sdk

from server import db
from server.models.utils import ModelBase


class UssdMenu(ModelBase):
    __tablename__ = 'ussd_menu'

    name = db.Column(db.String, nullable=False, index=True, unique=True)
    description = db.Column(db.String)
    parent_id = db.Column(db.Integer)

    ussd_sessions = db.relationship(
        'UssdSession', backref='ussd_menu', lazy=True, foreign_keys='UssdSession.ussd_menu_id'
    )

    """
        TODO: change how we do i18n
        keeping this as is from migration from grassroots economics
        but this system is really bad since we always need 
        all languages defined for all new menu items, no graceful fallback 
    """
    display_key = db.Column(db.String, nullable=False)

    @staticmethod
    def find_by_name(name: str) -> "UssdMenu":
        menus = UssdMenu.query.filter_by(name=name)
        if menus.count() == 0:
            sentry_sdk.capture_message("No USSD Menu with name {}".format(name))
            # should handle case if no invalid_request menu?
            return UssdMenu.query.filter_by(name='exit_invalid_request').first()
        else:
            return menus.first()

    def parent(self):
        return UssdMenu.query.filter_by(id=self.parent_id).first()

    def __repr__(self):
        return f"<UssdMenu {self.id}: {self.name} - {self.description}>"


class UssdSession(ModelBase):
    __tablename__ = 'ussd_session'

    session_id = db.Column(db.String, nullable=False, index=True, unique=True)
    service_code = db.Column(db.String, nullable=False)
    msisdn = db.Column(db.String, nullable=False)
    user_input = db.Column(db.String)
    state = db.Column(db.String, nullable=False)
    session_data = db.Column(JSON)

    ussd_menu_id = db.Column(db.Integer, db.ForeignKey('ussd_menu.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def set_data(self, key, value):
        if self.session_data is None:
            self.session_data = {}
        self.session_data[key] = value

        # https://stackoverflow.com/questions/42559434/updates-to-json-field-dont-persist-to-db
        flag_modified(self, "session_data")
        db.session.add(self)

    def get_data(self, key):
        if self.session_data is not None:
            return self.session_data.get(key)
        else:
            return None
