"""empty message

Revision ID: 925bbebe94bd
Revises: f8d4b8b18da8
Create Date: 2018-10-18 10:42:05.874322

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '925bbebe94bd'
down_revision = 'f8d4b8b18da8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('credit_transfer', sa.Column('recipient_user_id', sa.Integer(), nullable=True))
    op.add_column('credit_transfer', sa.Column('sender_user_id', sa.Integer(), nullable=True))
    op.alter_column('credit_transfer', 'sender_id', new_column_name='sender_transfer_account_id')
    op.alter_column('credit_transfer', 'recipient_id', new_column_name='recipient_transfer_account_id')
    op.create_foreign_key(None, 'credit_transfer', 'user', ['recipient_user_id'], ['id'])
    op.create_foreign_key(None, 'credit_transfer', 'user', ['sender_user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'credit_transfer', type_='foreignkey')
    op.drop_constraint(None, 'credit_transfer', type_='foreignkey')
    op.alter_column('credit_transfer', 'sender_transfer_account_id', new_column_name='sender_id')
    op.alter_column('credit_transfer', 'recipient_transfer_account_id', new_column_name='recipient_id')
    op.drop_column('credit_transfer', 'sender_user_id')
    op.drop_column('credit_transfer', 'recipient_user_id')
    # ### end Alembic commands ###
