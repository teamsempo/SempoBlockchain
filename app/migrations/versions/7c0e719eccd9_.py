"""empty message

Revision ID: 7c0e719eccd9
Revises: 8d672062eb10
Create Date: 2019-10-18 20:33:46.003766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c0e719eccd9'
down_revision = '8d672062eb10'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transfer_usage', sa.Column('default', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transfer_usage', 'default')
    # ### end Alembic commands ###
