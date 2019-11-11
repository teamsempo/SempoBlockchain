"""empty message

Revision ID: 403915103267
Revises: 38e2894e2a8f
Create Date: 2019-11-10 19:57:23.284390

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '403915103267'
down_revision = '38e2894e2a8f'
branch_labels = None
depends_on = None

def upgrade():
    tokentype = postgresql.ENUM('LIQUID', 'RESERVE', name='tokentype')
    tokentype.create(op.get_bind())

    op.add_column('token', sa.Column('token_type', sa.Enum('LIQUID', 'RESERVE', name='tokentype'), nullable=True))

def downgrade():
    op.drop_column('token', 'token_type')

    tokentype = postgresql.ENUM('LIQUID', 'RESERVE', name='tokentype')
    tokentype.drop(op.get_bind())