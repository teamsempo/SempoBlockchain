from factory.alchemy import SQLAlchemyModelFactory

from server import db
from server.models.user import User
from server.models.transfer_account import TransferAccount
from server.models.upload import UploadedImage
from server.models.kyc_application import KycApplication
from server.models.device_info import DeviceInfo
from server.models.referral import Referral
from server.models.feedback import Feedback


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session


# all the factories needed to get UserFactory working... move into own file if they get big
class DeviceInfoFactory(SQLAlchemyModelFactory):
    class Meta:
        model = DeviceInfo
        sqlalchemy_session = db.session


class KycApplicationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = KycApplication
        sqlalchemy_session = db.session


class UploadedImageFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UploadedImage
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

