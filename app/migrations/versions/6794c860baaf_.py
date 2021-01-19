"""Move custom attributes to new schema

Revision ID: 6794c860baaf
Revises: 380a71c24bba
Create Date: 2020-11-06 10:29:29.575412

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB
import json

# revision identifiers, used by Alembic.
revision = '6794c860baaf'
down_revision = '380a71c24bba'
branch_labels = None
depends_on = None

Base = declarative_base()

class CustomAttribute(Base):
    __tablename__ = 'custom_attribute'
    id              = sa.Column(sa.Integer, primary_key=True)
    name            = sa.Column(sa.String)
    attributes      = sa.orm.relationship("CustomAttributeUserStorage", back_populates="custom_attribute")
    cleaning_steps  = sa.Column(JSONB, default=None) # E.x. [ { "replace": ["this", "that"] }, { "lower": null } ]
    options         = sa.Column(JSONB, default=None) # E.x. ["male", "female", "other"]

class CustomAttributeUserStorage(Base):
    __tablename__ = 'custom_attribute_user_storage'
    id                  = sa.Column(sa.Integer, primary_key=True)
    custom_attribute_id = sa.Column(sa.Integer, sa.ForeignKey('custom_attribute.id'))
    custom_attribute    = sa.orm.relationship("CustomAttribute", back_populates="attributes")
    name                = sa.Column(sa.String) # Deprecated for key
    value               = sa.Column(sa.String)
    uploaded_image_id   = sa.Column(sa.Integer)

def index_exists(name):
    connection = op.get_bind()
    result = connection.execute(
        "SELECT exists(SELECT 1 from pg_indexes where indexname = '{}') as ix_exists;"
            .format(name)
    ).first()
    return bool(result.ix_exists)


def upgrade():
    conn = op.get_bind()
    session = Session(bind=conn)
    index_exists('ix_custom_attribute_user_storage_custom_attribute_id') or op.create_index(op.f('ix_custom_attribute_user_storage_custom_attribute_id'), 'custom_attribute_user_storage', ['custom_attribute_id'], unique=False)

    # If it hasn't been done before, migrate from the old custom attribute scheme to the new one
    try:
       if not session.query(CustomAttribute).all():
            print('Old style custom attributes still present. Migrating to new custom attributes scheme!')
            attributes = session.query(CustomAttributeUserStorage).all()
            attribute_cache = {} # Save { name : attribute } mapping so we don't have to query for it userCount times
            for user_attr in attributes:
                if not user_attr.custom_attribute:
                    if user_attr.name not in attribute_cache:
                        custom_attribute = session.query(CustomAttribute).filter(CustomAttribute.name == user_attr.name).first()
                        if not custom_attribute:
                            user_attr.custom_attribute = CustomAttribute()
                            user_attr.custom_attribute.name = user_attr.name
                            session.add(user_attr.custom_attribute)

                        attribute_cache[user_attr.name] = session.query(CustomAttribute).filter(CustomAttribute.name == user_attr.name).first()
                custom_attribute = attribute_cache[user_attr.name]
                user_attr.custom_attribute = custom_attribute
                try:
                    user_attr.value = json.loads(user_attr.value)
                except:
                    pass
                session.flush()

    except:
        print('Unable to automatically migrate to new-style custom attributes')


def downgrade():
    # op.drop_index(op.f('ix_custom_attribute_user_storage_custom_attribute_id'), table_name='custom_attribute_user_storage')
    pass
