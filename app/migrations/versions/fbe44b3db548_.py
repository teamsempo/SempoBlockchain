"""Index on lat and lng

Revision ID: fbe44b3db548
Revises: 3386e7f8b71f
Create Date: 2020-10-29 11:16:47.581145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbe44b3db548'
down_revision = '3386e7f8b71f'
branch_labels = None
depends_on = None

def index_exists(name):
    connection = op.get_bind()
    result = connection.execute(
        "SELECT exists(SELECT 1 from pg_indexes where indexname = '{}') as ix_exists;"
            .format(name)
    ).first()
    return bool(result.ix_exists)


def upgrade():
    index_exists('ix_user_lat') or op.create_index(op.f('ix_user_lat'), 'user', ['lat'], unique=False)
    index_exists('ix_user_lng') or op.create_index(op.f('ix_user_lng'), 'user', ['lng'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_user_lng'), table_name='user')
    op.drop_index(op.f('ix_user_lat'), table_name='user')
