"""Set pins where users have no pins

Revision ID: faef0f3afb43
Revises: 2f8c71039480
Create Date: 2020-10-26 16:51:11.125639

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'faef0f3afb43'
down_revision = '2f8c71039480'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('update "user" set pin_hash = password_hash where pin_hash is null;')


def downgrade():
    pass