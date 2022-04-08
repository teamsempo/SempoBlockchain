"""Add index to IP Address table

Revision ID: 00e04688706c
Revises: ceec78f714fc
Create Date: 2022-04-06 17:15:13.356698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00e04688706c'
down_revision = 'ceec78f714fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_ip_address__ip'), 'ip_address', ['_ip'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_ip_address__ip'), table_name='ip_address')
    # ### end Alembic commands ###
