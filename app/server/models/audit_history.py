from server import db
from server.models.utils import ModelBase

class AuditHistory(ModelBase):
    """
    Contains audit history for user and transfer account objects
    """
    __tablename__               = 'audit_history'

    change_by_id                = db.Column(db.Integer, db.ForeignKey("user.id"))
    change_by                   = db.relationship('User',
                                           primaryjoin='AuditHistory.change_by_id == User.id',
                                           lazy=True,
                                           uselist=False)
                                           
    column_name                 = db.Column(db.String)
    old_value                   = db.Column(db.String)
    new_value                   = db.Column(db.String)

    foreign_table_name          = db.Column(db.String, index=True)
    foreign_id                  = db.Column(db.Integer, index=True)
