"""Lengthen password columns, encrypt everything with pepper

Revision ID: c5266db8142f
Revises: 374a31e9843d
Create Date: 2020-01-22 10:28:51.397024

"""
from sqlalchemy.orm import Session
from alembic import op
import sqlalchemy as sa
import sys
import os
from cryptography.fernet import Fernet
from flask import current_app

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
from server.models.user import User
from server.models.token import Token
 
# revision identifiers, used by Alembic.
revision = 'c5266db8142f'
down_revision = '374a31e9843d'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    session = Session(bind=conn)

    op.alter_column('user', 'password_hash',
           existing_type=sa.VARCHAR(length=128),
           type_=sa.VARCHAR(length=200),
           existing_nullable=False)
    op.alter_column('user', 'pin_hash',
           existing_type=sa.VARCHAR(),
           type_=sa.VARCHAR(length=200),
           existing_nullable=False)
    session.commit()

    f = Fernet(current_app.config['PASSWORD_PEPPER'])
    for user in session.query(User).execution_options(show_all=True).all():
        if user.password_hash:
            user.password_hash = f.encrypt(user.password_hash.encode()).decode()
        if user.pin_hash:
            user.pin_hash = f.encrypt(user.pin_hash.encode()).decode()
    session.commit()

def downgrade():
    conn = op.get_bind()
    session = Session(bind=conn)

    f = Fernet(current_app.config['PASSWORD_PEPPER'])

    for user in session.query(User).execution_options(show_all=True).all():
        if user.password_hash:
            user.password_hash = f.decrypt(user.password_hash.encode()).decode()
        if user.pin_hash:
            user.pin_hash = f.decrypt(user.pin_hash.encode()).decode()
    session.commit()

    op.alter_column('user', 'password_hash',
           existing_type=sa.VARCHAR(length=200),
           type_=sa.VARCHAR(length=128),
           existing_nullable=False)
    op.alter_column('user', 'pin_hash',
           existing_type=sa.VARCHAR(length=200),
           type_=sa.VARCHAR(),
           existing_nullable=False)
    session.commit()
