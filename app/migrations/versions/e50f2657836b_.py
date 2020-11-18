"""Add cleaning steps and multiple-choice options

Revision ID: e50f2657836b
Revises: f1ed219d6cf4
Create Date: 2020-09-04 18:38:54.109793

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e50f2657836b'
down_revision = 'f1ed219d6cf4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('custom_attribute', sa.Column('cleaning_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('custom_attribute', sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('custom_attribute', 'options')
    op.drop_column('custom_attribute', 'cleaning_steps')
    # ### end Alembic commands ###
