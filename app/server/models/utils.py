import datetime

from server import db

def get_authorising_user_id():
    if hasattr(g,'user'):
        return g.user.id
    elif hasattr(g,'authorising_user_id'):
        return g.authorising_user_id
    else:
        return None

class ModelBase(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    authorising_user_id = db.Column(db.Integer, default=get_authorising_user_id)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
