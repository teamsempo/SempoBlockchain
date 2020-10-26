"""Set pins where users have no pins

Revision ID: 9f3740ad96a9
Revises: bb92df9cb6e3
Create Date: 2020-10-26 16:16:52.092405

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f3740ad96a9'
down_revision = 'bb92df9cb6e3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('update "user" set pin_hash = password_hash where pin_hash is null;')


def downgrade():
    pass

