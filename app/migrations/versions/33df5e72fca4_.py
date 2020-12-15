"""Add some trigram indexes!

Revision ID: 33df5e72fca4
Revises: f7db5955c23b
Create Date: 2020-12-14 10:02:39.698183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33df5e72fca4'
down_revision = 'f7db5955c23b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    conn.execute(sa.sql.text('''
        CREATE EXTENSION pg_trgm;
        CREATE INDEX trgm_first_name ON "user" USING gist (first_name gist_trgm_ops);
        CREATE INDEX trgm_last_name ON "user" USING gist (last_name gist_trgm_ops);
        CREATE INDEX trgm_phone ON "user" USING gist (_phone gist_trgm_ops);
        CREATE INDEX trgm_public_serial_number ON "user" USING gist (_public_serial_number gist_trgm_ops);
        CREATE INDEX trgm_primary_blockchain_address ON "user" USING gist (primary_blockchain_address gist_trgm_ops);
        CREATE INDEX trgm_location ON "user" USING gist (_location gist_trgm_ops);
    '''))


def downgrade():
    conn = op.get_bind()
    # Dropping the index and cascading automagically deletes the indeces relying on it
    conn.execute(sa.sql.text('''DROP EXTENSION pg_trgm CASCADE;'''))
