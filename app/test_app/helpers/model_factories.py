from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from faker.providers import phone_number

from server import db
from server.models.device_info import DeviceInfo
from server.models.feedback import Feedback
from server.models.kyc_application import KycApplication
from server.models.organisation import Organisation
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_usage import TransferUsage
from server.models.credit_transfer import CreditTransfer
from server.models.upload import UploadedResource
from server.models.user import User
from server.models.ussd import UssdSession, UssdMenu
from server.models.token import Token

fake = Faker()
fake.add_provider(phone_number)


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session


class DeviceInfoFactory(SQLAlchemyModelFactory):
    class Meta:
        model = DeviceInfo
        sqlalchemy_session = db.session


class UploadedResourceFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UploadedResource
        sqlalchemy_session = db.session


class TransferAccountFactory(SQLAlchemyModelFactory):
    class Meta:
        model = TransferAccount
        sqlalchemy_session = db.session

class CreditTransferFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CreditTransfer
        sqlalchemy_session = db.session


class FeedbackFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Feedback
        sqlalchemy_session = db.session


class TransferUsageFactory(SQLAlchemyModelFactory):
    class Meta:
        model = TransferUsage
        sqlalchemy_session = db.session


class KycApplicationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = KycApplication
        sqlalchemy_session = db.session


class OrganisationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organisation
        sqlalchemy_session = db.session
    name = 'Francines Company'


class UssdMenuFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UssdMenu
        sqlalchemy_session = db.session

    name = 'start'


class UssdSessionFactoryBase(SQLAlchemyModelFactory):
    class Meta:
        model = UssdSession
        sqlalchemy_session = db.session

    session_id = Sequence(lambda n: n)
    service_code = "123"
    msisdn = fake.msisdn()

def UssdSessionFactory(**kwargs):
    # Uses Class Naming Convention because it's actually a delayed execution Class
    def inner():
        unique_name = Sequence(lambda n: f'FooSSD{n}')
        ussd_menu = UssdMenuFactory(name=unique_name, display_key=unique_name)

        return UssdSessionFactoryBase(ussd_menu=ussd_menu, **kwargs)

    return inner()

class TokenFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Token
        sqlalchemy_session = db.session
