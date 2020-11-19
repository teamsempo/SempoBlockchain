"""merge heads again

Revision ID: f1d798cd9521
Revises: 031b08023aa1, 3966df3f41a0
Create Date: 2020-11-19 09:03:11.501642

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1d798cd9521'
down_revision = ('031b08023aa1', '3966df3f41a0')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
