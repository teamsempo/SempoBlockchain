from server import db
from server.models.utils import ModelBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class SynchronizedBlock(ModelBase):
    __tablename__ = 'synchronized_block'
    block_number = db.Column(db.Integer)
    synchronization_filter_id = db.Column(db.Integer, ForeignKey('synchronization_filter.id'))
    synchronization_filter = relationship("SynchronizationFilter", back_populates="blocks")
    status = db.Column(db.String)