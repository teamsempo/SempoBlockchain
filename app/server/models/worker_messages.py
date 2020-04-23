from sqlalchemy.dialects.postgresql import JSON

from server import db
from server.models.utils import ModelBase
from server.models.credit_transfer import CreditTransfer

class WorkerMessages(ModelBase):
    __tablename__ = 'worker_messages'
    credit_transfer_id = db.Column(db.Integer, db.ForeignKey(CreditTransfer.id))
    message = db.Column(db.String)
    error = db.Column(db.String)
    worker_timestamp = db.Column(db.DateTime)
