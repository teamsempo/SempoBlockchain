from factory.alchemy import SQLAlchemyModelFactory
from factory import Sequence
from faker.providers import phone_number
from faker import Faker

from server import db
from server.models.ussd import UssdSession

fake = Faker()
fake.add_provider(phone_number)


class UssdSessionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UssdSession
        sqlalchemy_session = db.session

    session_id = Sequence(lambda n: n)
    service_code = "123"
    msisdn = fake.msisdn()
    # we might want to tie this to an actual ussd menu for some tests?
    ussd_menu_id = 1