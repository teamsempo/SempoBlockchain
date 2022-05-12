import sentry_sdk
from server import db, celery_app, mt
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import INET

from server.models.utils import ModelBase


class IpAddress(ModelBase):
    __tablename__               = 'ip_address'

    _ip                         = db.Column(INET, index=True)
    country                     = db.Column(db.String)

    user_id                     = db.Column(db.Integer, db.ForeignKey('user.id'))

    @staticmethod
    def check_user_ips(user, ip_address):
        # check whether ip address is saved for a given user
        return IpAddress.query.filter_by(ip=ip_address, user_id=user.id).first()


    @hybrid_property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):

        self._ip = ip

        if ip is not None:

            try:
                mt.set_ip_location(self.id, ip)
            except Exception as e:
                print(e)
                sentry_sdk.capture_exception(e)
                pass
