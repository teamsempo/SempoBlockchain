import random, string

from server import db
from server.models.utils import ModelBase, OneOrgBase


class EmailWhitelist(OneOrgBase, ModelBase):
    __tablename__ = 'email_whitelist'

    email = db.Column(db.String)

    tier = db.Column(db.String, default='view')
    referral_code = db.Column(db.String)

    allow_partial_match = db.Column(db.Boolean, default=False)
    used = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(EmailWhitelist, self).__init__(**kwargs)
        self.referral_code = ''.join(random.choices(
            string.ascii_letters + string.digits, k=16))

    def __repr__(self):
        return f'<EmailWhitelist {self.id}: {self.email}, {self.tier}, {"used" if self.used else "unused"}>'


