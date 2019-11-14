"""empty message

Revision ID: 3f7fe44202bd
Revises: d1bf5c21d9f3
Create Date: 2019-11-14 13:41:44.231455

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f7fe44202bd'
down_revision = 'd1bf5c21d9f3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('failed_pin_attempts', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('pin_hash', sa.String(), nullable=True))
    op.add_column('user', sa.Column('pin_reset_tokens', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'pin_reset_tokens')
    op.drop_column('user', 'pin_hash')
    op.drop_column('user', 'failed_pin_attempts')
    # ### end Alembic commands ###
