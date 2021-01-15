"""Do nothing

Revision ID: 031b08023aa1
Revises: 6488be258421
Create Date: 2020-11-18 15:56:53.861776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031b08023aa1'
down_revision = '6488be258421'
branch_labels = None
depends_on = None


def upgrade():
    return True


def downgrade():
    return True

