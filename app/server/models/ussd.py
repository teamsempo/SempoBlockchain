from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified

from server import db, sentry
from server.models.utils import ModelBase
from sqlalchemy.orm.attributes import flag_modified


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
    display_key = db.Column(db.String, nullable=False)

    @staticmethod
    def find_by_name(name: str) -> "UssdMenu":
        menus = UssdMenu.query.filter_by(name=name)
        if menus.count() == 0:
            sentry.captureMessage("No USSD Menu with name {}".format(name))
            # should handle case if no invalid_request menu?
            return UssdMenu.query.filter_by(name='exit_invalid_request').first()
        else:
            return menus.first()

    def parent(self):
        return UssdMenu.query.filter_by(id=self.parent_id).first()


class UssdSession(ModelBase):
    __tablename__ = 'ussd_sessions'

    session_id = db.Column(db.String, nullable=False, index=True, unique=True)
    user_id = db.Column(db.Integer)
    service_code = db.Column(db.String, nullable=False)
    msisdn = db.Column(db.String, nullable=False)
    user_input = db.Column(db.String)
    ussd_menu_id = db.Column(db.Integer, nullable=False)
    state = db.Column(db.String, nullable=False)
    session_data = db.Column(JSON)

    def set_data(self, key, value):
        if self.session_data is None:
            self.session_data = {}
        self.session_data[key] = value

        # https://stackoverflow.com/questions/42559434/updates-to-json-field-dont-persist-to-db
        flag_modified(self, "session_data")
        db.session.add(self)

    def get_data(self, key):
        if self.session_data is not None:
            return self.session_data[key]
        else:
            return None
