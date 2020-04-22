"""empty message

Revision ID: dc7ba64ef73d
Revises: 6d8a938930ff
Create Date: 2020-04-22 13:27:47.766051

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'dc7ba64ef73d'
down_revision = '6d8a938930ff'
branch_labels = None
depends_on = None


def upgrade():
    blockchain_status = postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='blockchain_status')
    blockchain_status.create(op.get_bind())

    op.add_column('credit_transfer', sa.Column('blockchain_status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', name='blockchain_status'), nullable=True))
    op.add_column('credit_transfer', sa.Column('last_worker_update', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('credit_transfer', 'last_worker_update')
    op.drop_column('credit_transfer', 'blockchain_status')
    blockchain_status = postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='blockchain_status')
    blockchain_status.drop(op.get_bind())


