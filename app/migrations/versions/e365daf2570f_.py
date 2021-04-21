"""Remove require_multiple_transfer_approvals org setting

Revision ID: e365daf2570f
Revises: 7e2d2b201c80
Create Date: 2021-04-21 15:29:47.423954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e365daf2570f'
down_revision = '7e2d2b201c80'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('organisation', 'require_multiple_transfer_approvals')

def downgrade():
    op.add_column('organisation', sa.Column('require_multiple_transfer_approvals', sa.BOOLEAN(), autoincrement=False, nullable=True))
