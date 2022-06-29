import datetime

from server import db
from server.models.utils import ModelBase

class BlacklistToken(ModelBase):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'blacklist_tokens'

    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, index=True)

    @staticmethod
    def check_blacklist(token):
        # check whether auth token has been blacklisted
        user_id = token['id']
        token_iat = token['iat']
        res = BlacklistToken.query\
            .filter_by(user_id=str(user_id))\
            .order_by(BlacklistToken.id.desc())\
            .first()

        if res:
            if token_iat <= res.blacklisted_on.timestamp():
                return True
        return False

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        self.blacklisted_on = datetime.datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)
