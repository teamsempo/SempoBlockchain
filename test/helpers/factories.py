from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from faker.providers import phone_number

from server import db
from server.models.device_info import DeviceInfo
from server.models.feedback import Feedback
from server.models.kyc_application import KycApplication
from server.models.organisation import Organisation
from server.models.referral import Referral
from server.models.transfer_account import TransferAccount
from server.models.transfer_usage import TransferUsage
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


class ReferralFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Referral
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


class UssdSessionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UssdSession
        sqlalchemy_session = db.session

    session_id = Sequence(lambda n: n)
    service_code = "123"
    msisdn = fake.msisdn()
    # we might want to tie this to an actual ussd menu for some tests?
    ussd_menu_id = 1


class UssdMenuFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UssdMenu
        sqlalchemy_session = db.session

    name = 'start'


class TokenFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Token
        sqlalchemy_session = db.session
