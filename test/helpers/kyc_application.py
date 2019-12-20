from factory.alchemy import SQLAlchemyModelFactory

from server import db
from server.models.kyc_application import KycApplication


class KycApplicationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = KycApplication
        sqlalchemy_session = db.session