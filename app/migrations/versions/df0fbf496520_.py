"""empty message

Revision ID: df0fbf496520
Revises: 5f4b4c9f586d
Create Date: 2020-01-24 13:15:27.081704

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df0fbf496520'
down_revision = '5f4b4c9f586d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('is_market_enabled', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'is_market_enabled')
    # ### end Alembic commands ###
