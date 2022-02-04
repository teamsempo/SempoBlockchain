from server.models.utils import ModelBase
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSONB
import enum, random, string
from server.exceptions import PaymentMethodException
from server.constants import PAYMENT_METHODS
from server import db
from server.models.credit_transfer import CreditTransfer
from server.models.token import Token
from server.utils.flutterwave import make_withdrawal
import datetime

class FiatRampStatusEnum(enum.Enum):
    PENDING = 'PENDING'
    FAILED = 'FAILED'
    COMPLETE = 'COMPLETE'

class FiatRampDirection(enum.Enum):
    INGRESS = 'INGRESS'
    EGRESS = 'EGRESS'


class FiatRamp(ModelBase):
    """
    FiatRamp model handles multiple on and off ramps (exchanging fiat for crypto)
    e.g. used ONLY to exchange Fiat AUD for Synthetic AUD.

    credit_transfer_id: references addition or withdrawal of user funds in the exchange process
    token_id: reference blockchain token
    """

    __tablename__               = 'fiat_ramp'

    _payment_method             = db.Column(db.String)
    payment_amount              = db.Column(db.Integer, default=0)
    payment_reference           = db.Column(db.String)
    payment_status              = db.Column(db.Enum(FiatRampStatusEnum), default=FiatRampStatusEnum.PENDING)
    payment_direction           = db.Column(db.Enum(FiatRampDirection), default=FiatRampDirection.EGRESS)
    credit_transfer_id          = db.Column(db.Integer, db.ForeignKey(CreditTransfer.id))
    token_id                    = db.Column(db.Integer, db.ForeignKey(Token.id))

    payment_metadata            = db.Column(JSONB)

    @hybrid_property
    def payment_method(self):
        return self._payment_method

    @payment_method.setter
    def payment_method(self, payment_method):
        if payment_method not in PAYMENT_METHODS:
            raise PaymentMethodException('Payment method {} not found'.format(payment_method))

        self._payment_method = payment_method

    def resolve_as_complete(self):
        if self.payment_method == 'FLUTTERWAVE':
            try:
                make_withdrawal(self)
            except Exception as e:
                self.resolve_as_rejected(str(e))
                return
        self.updated = datetime.datetime.utcnow()
        self.payment_status = FiatRampStatusEnum.COMPLETE

    def resolve_as_rejected(self, message=None):
        self.updated = datetime.datetime.utcnow()
        self.payment_status = FiatRampStatusEnum.FAILED

        if message:
            if not self.payment_metadata: self.payment_metadata = {}
            self.payment_metadata['message'] = message

    def __init__(self, **kwargs):
        super(FiatRamp, self).__init__(**kwargs)

        def random_string(length):
            return ''.join(random.choices(string.ascii_letters, k=length))

        self.payment_reference = random_string(5) + '-' + random_string(5)
