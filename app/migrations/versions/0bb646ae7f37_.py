"""empty message

Revision ID: 0bb646ae7f37
Revises: 04c372052fc6
Create Date: 2019-10-06 15:54:02.958251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bb646ae7f37'
down_revision = '04c372052fc6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('fiat_ramp', sa.Column('payment_reference', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('fiat_ramp', 'payment_reference')
    # ### end Alembic commands ###
