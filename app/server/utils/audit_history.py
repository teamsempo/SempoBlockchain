from server.models.audit_history import AuditHistory
from server import db
from sqlalchemy import event
from flask import g

# Audit history doesn't currently support foreign keys (or in the case of custom attributes, nested foreign keys)
# In the interest of preventing complexity to serve edge cases, this functions allows manual addition of history entries.
def manually_add_history_entry(foreign_table_name, foreign_id, column_name, old_value, new_value):
    if old_value != new_value:
        db.session.add(AuditHistory(
            change_by_id=g.user.id if g.get('user') else None,
            column_name=column_name,
            old_value=str(old_value),
            new_value=str(new_value),
            foreign_table_name=foreign_table_name,
            foreign_id=foreign_id
        ))
    

# Call this with the associated model to start tracking updates
# Add audit_history_columns to the class to indicate which rows to store
def track_updates(model):
    @event.listens_for(model, 'before_update')
    def before_update(mapper, connection, target):
        change_by_id = g.user.id if g.get('user') else None
        state = db.inspect(target)
        ah = []
        nuke_history = False
        for attr in state.attrs:
            hist = attr.load_history()
            if not hist.has_changes():
                continue

            if attr.key in model.audit_history_columns:
                old_value = hist.deleted[0] if hist.deleted else None
                new_value = hist.added[0] if hist.added else None
                # Covers account types edgecase, we only really care about the values
                # The goal here is to make something human-readable out of `{'VENDOR': 'supervendor'}`
                if(attr.key == '_held_roles'):
                    if old_value:
                        old_value = ', '.join(old_value.values())
                    if new_value:
                        new_value = ', '.join(new_value.values())

                # Nuking history involves zeroing every column
                # We don't want to save that, so we only save the _deleted column and delete the rest
                if(attr.key == '_deleted'):
                    nuke_history = True
                    ah = []

                ah.append(AuditHistory(
                    change_by_id=change_by_id,
                    column_name=attr.key,
                    old_value=str(old_value) if old_value != None else None,
                    new_value=str(new_value) if new_value != None else None,
                    foreign_table_name=target.__tablename__,
                    foreign_id=target.id
                ))
                
            if nuke_history:
                break

        # We want to add audit history after flush since adding to the database in
        # before_update is unsafe behavior
        @event.listens_for(db.session, "after_flush", once=True)
        def receive_after_flush(session, context):
            for audit_history in ah:
                db.session.add(audit_history)
            # Deletes history for objects which are being deleted, but keeps the actual record of the deletion
            if nuke_history:
                db.session.query(AuditHistory)\
                    .filter(AuditHistory.foreign_id == target.id)\
                    .filter(AuditHistory.foreign_table_name == target.__tablename__)\
                    .filter(AuditHistory.column_name != '_deleted')\
                    .delete()

# Gets audit history using the row ID and it's associated tablename
def get_audit_history(id, table_name):
    return db.session.query(AuditHistory)\
        .filter(AuditHistory.foreign_id == id)\
        .filter(AuditHistory.foreign_table_name == table_name)\
        .order_by(AuditHistory.id)\
        .all()
