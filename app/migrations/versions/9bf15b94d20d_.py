"""Add valid_roles to org!

Revision ID: 9bf15b94d20d
Revises: fbd0f6a88346
Create Date: 2020-08-18 17:20:21.288115

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9bf15b94d20d'
down_revision = 'fbd0f6a88346'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organisation', sa.Column('valid_roles', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organisation', 'valid_roles')
    # ### end Alembic commands ###
