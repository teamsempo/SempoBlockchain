from server import db, sentry, celery_app
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import INET

from server.models.utils import ModelBase

class IpAddress(ModelBase):
    __tablename__               = 'ip_address'

    _ip                         = db.Column(INET)
    country                     = db.Column(db.String)

    user_id                     = db.Column(db.Integer, db.ForeignKey('user.id'))

    @staticmethod
    def check_user_ips(user, ip_address):
        # check whether ip address is saved for a given user
        res = IpAddress.query.filter_by(ip=ip_address, user_id=user.id).first()
        if res:
            return True
        else:
            return False

    @hybrid_property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):

        self._ip = ip

        if ip is not None:

            try:
                task = {'ip_address_id': self.id, 'ip': ip}
                ip_location_task = celery_app.signature('worker.celery_tasks.ip_location', args=(task,))

                ip_location_task.delay()
            except Exception as e:
                print(e)
                sentry.captureException()
                pass
