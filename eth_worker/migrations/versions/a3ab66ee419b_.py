"""Add a bunch of indexes

Revision ID: a3ab66ee419b
Revises: c81dbf171b47
Create Date: 2020-11-12 14:28:01.524431

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3ab66ee419b'
down_revision = 'c81dbf171b47'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_blockchain_task_reverses_id'), 'blockchain_task', ['reverses_id'], unique=False)
    op.create_index(op.f('ix_blockchain_task_signing_wallet_id'), 'blockchain_task', ['signing_wallet_id'], unique=False)
    op.create_index(op.f('ix_blockchain_transaction__status'), 'blockchain_transaction', ['_status'], unique=False)
    op.create_index(op.f('ix_blockchain_transaction_blockchain_task_id'), 'blockchain_transaction', ['blockchain_task_id'], unique=False)
    op.create_index(op.f('ix_blockchain_transaction_first_block_hash'), 'blockchain_transaction', ['first_block_hash'], unique=False)
    op.create_index(op.f('ix_blockchain_transaction_nonce_consumed'), 'blockchain_transaction', ['nonce_consumed'], unique=False)
    op.create_index(op.f('ix_blockchain_transaction_signing_wallet_id'), 'blockchain_transaction', ['signing_wallet_id'], unique=False)
    op.create_index(op.f('ix_blockchain_transaction_submitted_date'), 'blockchain_transaction', ['submitted_date'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_blockchain_transaction_submitted_date'), table_name='blockchain_transaction')
    op.drop_index(op.f('ix_blockchain_transaction_signing_wallet_id'), table_name='blockchain_transaction')
    op.drop_index(op.f('ix_blockchain_transaction_nonce_consumed'), table_name='blockchain_transaction')
    op.drop_index(op.f('ix_blockchain_transaction_first_block_hash'), table_name='blockchain_transaction')
    op.drop_index(op.f('ix_blockchain_transaction_blockchain_task_id'), table_name='blockchain_transaction')
    op.drop_index(op.f('ix_blockchain_transaction__status'), table_name='blockchain_transaction')
    op.drop_index(op.f('ix_blockchain_task_signing_wallet_id'), table_name='blockchain_task')
    op.drop_index(op.f('ix_blockchain_task_reverses_id'), table_name='blockchain_task')
    # ### end Alembic commands ###
