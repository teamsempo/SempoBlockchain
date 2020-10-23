"""jsonb to json

Revision ID: bfc859dcb6ac
Revises: 6e81096af584
Create Date: 2020-10-23 16:47:34.915758

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'bfc859dcb6ac'
down_revision = '6e81096af584'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('user', 'matched_profile_pictures', type_=postgresql.JSONB, postgresql_using='matched_profile_pictures::text::jsonb')

def downgrade():
    op.alter_column('user', 'matched_profile_pictures', type_=postgresql.JSON, postgresql_using='matched_profile_pictures::text::json')
