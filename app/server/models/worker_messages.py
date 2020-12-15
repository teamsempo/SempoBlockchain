from server import db
from server.models.utils import ModelBase

class WorkerMessages(ModelBase):
    __tablename__ = 'worker_messages'
    message = db.Column(db.String)
    error = db.Column(db.String)
    worker_timestamp = db.Column(db.DateTime)
    blockchain_task_uuid = db.Column(db.String, index=True)
