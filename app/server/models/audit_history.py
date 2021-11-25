from server import db
from server.models.utils import ModelBase
from sqlalchemy import event
from flask import g

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

    user_id                     = db.Column(db.Integer, db.ForeignKey("user.id"))
    transfer_account_id         = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))


# Call this with the associated model to start tracking updates
# Add audit_history_columns to the class to indicate which rows to store
def track_updates(model):
    @event.listens_for(model, 'before_update')
    def before_update(mapper, connection, target):
        transfer_account_id = target.id if target.__tablename__ == 'transfer_account' else None
        user_id = target.id if target.__tablename__ == 'user' else None
        change_by_id = g.user.id if g.get('user') else None
        state = db.inspect(target)
        ah = []
        for attr in state.attrs:
            hist = attr.load_history()
            if not hist.has_changes():
                continue
            if attr.key in model.audit_history_columns:
                ah.append(AuditHistory(
                    change_by_id=change_by_id,
                    column_name=attr.key,
                    old_value=str(hist.deleted[0]) if hist.deleted else None,
                    new_value=str(hist.added[0]) if hist.added else None,
                    transfer_account_id=transfer_account_id,
                    user_id=user_id
                ))

        # We want to add audit history after flush since adding to the database in
        # before_update is unsafe behavior
        @event.listens_for(db.session, "after_flush", once=True)
        def receive_after_flush(session, context):
            for audit_history in ah:
                db.session.add(audit_history)
