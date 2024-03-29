"""empty message

Revision ID: b930c0a15ab8
Revises: c14405edda7c
Create Date: 2021-08-03 17:26:40.095764

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b930c0a15ab8'
down_revision = 'c14405edda7c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_synchronized_block_block_number', table_name='synchronized_block')
    op.drop_index('ix_synchronized_block_synchronization_filter_id', table_name='synchronized_block')
    op.drop_table('synchronized_block')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('synchronized_block',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('block_number', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_synchronized', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('synchronization_filter_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('decimals', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['synchronization_filter_id'], ['synchronization_filter.id'], name='synchronized_block_synchronization_filter_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='synchronized_block_pkey')
    )
    op.create_index('ix_synchronized_block_synchronization_filter_id', 'synchronized_block', ['synchronization_filter_id'], unique=False)
    op.create_index('ix_synchronized_block_block_number', 'synchronized_block', ['block_number'], unique=False)
    # ### end Alembic commands ###
