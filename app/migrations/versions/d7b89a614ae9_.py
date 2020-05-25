"""Adds messages foreign key for worker callback

Revision ID: d7b89a614ae9
Revises: 07dd5846b6db
Create Date: 2020-05-12 12:18:32.199170

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd7b89a614ae9'
down_revision = '07dd5846b6db'
branch_labels = None
depends_on = None


def upgrade():
    blockchain_status = postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='blockchainstatus')
    blockchain_status.create(op.get_bind())

    op.create_table('worker_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('authorising_user_id', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('message', sa.String(), nullable=True),
    sa.Column('error', sa.String(), nullable=True),
    sa.Column('worker_timestamp', sa.DateTime(), nullable=True),
    sa.Column('blockchain_task_uuid', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('credit_transfer', sa.Column('blockchain_hash', sa.String(), nullable=True))
    op.add_column('credit_transfer', sa.Column('blockchain_status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', name='blockchainstatus'), nullable=True))
    op.add_column('credit_transfer', sa.Column('last_worker_update', sa.DateTime(), nullable=True))
    op.add_column('exchange', sa.Column('blockchain_hash', sa.String(), nullable=True))
    op.add_column('exchange', sa.Column('blockchain_status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', name='blockchainstatus'), nullable=True))
    op.add_column('exchange', sa.Column('last_worker_update', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_worker_messages_table_blockchain_task_uuid'), 'worker_messages', ['blockchain_task_uuid'], unique=False)

def downgrade():
    op.drop_column('exchange', 'last_worker_update')
    op.drop_column('exchange', 'blockchain_status')
    op.drop_column('exchange', 'blockchain_hash')
    op.drop_column('credit_transfer', 'last_worker_update')
    op.drop_column('credit_transfer', 'blockchain_status')
    op.drop_column('credit_transfer', 'blockchain_hash')
    op.drop_table('worker_messages')
    blockchain_status = postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='blockchainstatus')
    blockchain_status.drop(op.get_bind())
