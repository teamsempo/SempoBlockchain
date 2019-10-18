from factory.alchemy import SQLAlchemyModelFactory

from server import db
from server.models.ussd import UssdSession


class UssdSessionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UssdSession
        sqlalchemy_session = db.session
