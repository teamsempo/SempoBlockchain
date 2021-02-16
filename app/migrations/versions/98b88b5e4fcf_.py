"""empty message

Revision ID: 98b88b5e4fcf
Revises: 279b30132f29
Create Date: 2021-02-15 15:05:57.430038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98b88b5e4fcf'
down_revision = '279b30132f29'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_custom_attribute_filter_visibility'), 'custom_attribute', ['filter_visibility'], unique=False)
    op.create_index(op.f('ix_custom_attribute_group_visibility'), 'custom_attribute', ['group_visibility'], unique=False)
    op.add_column('disbursement', sa.Column('state', sa.String(), nullable=True))
    op.drop_column('disbursement', 'is_executed')
    op.drop_index('trgm_first_name', table_name='user')
    op.drop_index('trgm_last_name', table_name='user')
    op.drop_index('trgm_location', table_name='user')
    op.drop_index('trgm_phone', table_name='user')
    op.drop_index('trgm_primary_blockchain_address', table_name='user')
    op.drop_index('trgm_public_serial_number', table_name='user')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('trgm_public_serial_number', 'user', ['_public_serial_number'], unique=False)
    op.create_index('trgm_primary_blockchain_address', 'user', ['primary_blockchain_address'], unique=False)
    op.create_index('trgm_phone', 'user', ['_phone'], unique=False)
    op.create_index('trgm_location', 'user', ['_location'], unique=False)
    op.create_index('trgm_last_name', 'user', ['last_name'], unique=False)
    op.create_index('trgm_first_name', 'user', ['first_name'], unique=False)
    op.add_column('disbursement', sa.Column('is_executed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('disbursement', 'state')
    op.drop_index(op.f('ix_custom_attribute_group_visibility'), table_name='custom_attribute')
    op.drop_index(op.f('ix_custom_attribute_filter_visibility'), table_name='custom_attribute')
    # ### end Alembic commands ###
