"""Add disbursement errors

Revision ID: 1a762e73a3be
Revises: 0010eea24b21
Create Date: 2021-07-13 14:49:05.893409

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a762e73a3be'
down_revision = '0010eea24b21'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('disbursement', sa.Column('errors', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('disbursement', 'errors')
    # ### end Alembic commands ###
