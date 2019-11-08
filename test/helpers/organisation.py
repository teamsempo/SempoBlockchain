from factory.alchemy import SQLAlchemyModelFactory

from server import db
from server.models.organisation import Organisation


class OrganisationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organisation
        sqlalchemy_session = db.session
