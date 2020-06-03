from server import db
from server.models.utils import ModelBase
from sqlalchemy.orm import relationship

class SynchronizationFilter(ModelBase):
    __tablename__ = 'synchronization_filter'
    contract_address = db.Column(db.String)
    contract_type = db.Column(db.String)
    last_block_synchronized = db.Column(db.Integer)
    filter_parameters = db.Column(db.String)
    blocks = relationship("SynchronizedBlock", back_populates="synchronization_filter")