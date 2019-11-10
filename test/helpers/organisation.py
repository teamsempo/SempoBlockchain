from factory.alchemy import SQLAlchemyModelFactory
from factory import Sequence
from faker.providers import phone_number
from faker import Faker

from server import db
from server.models.organisation import Organisation

fake = Faker()
fake.add_provider(phone_number)


class OrganisationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organisation
        sqlalchemy_session = db.session