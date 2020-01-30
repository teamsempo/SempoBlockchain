"""empty message

Revision ID: 0d586d339657
Revises: 2591b8be0eb8
Create Date: 2020-01-30 13:00:31.256353

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d586d339657'
down_revision = '2591b8be0eb8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('data_sharing_accepted', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'data_sharing_accepted')
    # ### end Alembic commands ###
