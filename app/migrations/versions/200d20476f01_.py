"""Add partial to transfer enum

Revision ID: 200d20476f01
Revises: 9a0ec8ac3881
Create Date: 2021-04-09 14:01:05.128693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '200d20476f01'
down_revision = '9a0ec8ac3881'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE transferstatusenum ADD VALUE 'PARTIAL'")


def downgrade():
    pass
