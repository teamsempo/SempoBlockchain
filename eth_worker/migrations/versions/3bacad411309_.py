"""empty message

Revision ID: 3bacad411309
Revises: 606591437586
Create Date: 2019-09-29 16:43:33.423853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bacad411309'
down_revision = '606591437586'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('blockchain_address', 'blockchain_wallet')

def downgrade():
    op.rename_table('blockchain_wallet', 'blockchain_address')

