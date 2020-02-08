"""Adds external auth password

Revision ID: 961ab9adc300
Revises: df0fbf496520
Create Date: 2020-01-25 17:29:33.195793

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from server.models.organisation import Organisation
from server.utils.misc import encrypt_string
import secrets

# revision identifiers, used by Alembic.
revision = '961ab9adc300'
down_revision = '326a61cf9fde'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    session = Session(bind=conn)

    op.add_column('organisation', sa.Column('external_auth_username', sa.String(), nullable=True))
    op.add_column('organisation', sa.Column('_external_auth_password', sa.String(), nullable=True))

    for org in session.query(Organisation).execution_options(show_all=True).all():
        org.external_auth_username = 'admin_'+org.name.lower().replace(' ', '_')
        org.external_auth_password = secrets.token_hex(16)
    session.commit()


def downgrade():
    op.drop_column('organisation', 'external_auth_username')
    op.drop_column('organisation', '_external_auth_password')
