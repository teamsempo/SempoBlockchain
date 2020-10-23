"""Add search indexes to user

Revision ID: 6e81096af584
Revises: db04b5b96ab8
Create Date: 2020-10-23 12:08:35.931724

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6e81096af584'
down_revision = 'db04b5b96ab8'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    op.add_column('user', sa.Column('tsv_default_transfer_account_id', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_email', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_first_name', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_last_name', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_location', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_phone', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_primary_blockchain_address', postgresql.TSVECTOR(), nullable=True))
    op.add_column('user', sa.Column('tsv_public_serial_number', postgresql.TSVECTOR(), nullable=True))
    
    conn.execute(sa.sql.text('''CREATE INDEX ix_tsv_email ON "user" USING gin(tsv_email);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_tsv_phone ON "user" USING gin(tsv_phone);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_tsv_firstname ON "user" USING gin(tsv_first_name);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_tsv_lastname ON "user" USING gin(tsv_last_name);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_public_serial_number ON "user" USING gin(tsv_public_serial_number);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_location ON "user" USING gin(tsv_location);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_primary_blockchain_address ON "user" USING gin(tsv_primary_blockchain_address);'''))
    conn.execute(sa.sql.text('''CREATE INDEX ix_default_transfer_account_id ON "user" USING gin(tsv_default_transfer_account_id);'''))

    # Will take a bit on large data sets
    print('Back-populating tsv_default_transfer_account_id')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_default_transfer_account_id = to_tsvector(CAST (u1.default_transfer_account_id AS VARCHAR(10)));'''))
    print('Back-populating tsv_email')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_email = to_tsvector(u1.email);'''))
    print('Back-populating tsv_phone')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_phone = to_tsvector(u1._phone);'''))
    print('Back-populating tsv_first_name')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_first_name = to_tsvector(u1.first_name);'''))
    print('Back-populating tsv_last_name')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_last_name = to_tsvector(u1.last_name);'''))
    print('Back-populating tsv_public_serial_number')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_public_serial_number = to_tsvector(u1._public_serial_number);'''))
    print('Back-populating tsv_location')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_location = to_tsvector(u1._location);'''))
    print('Back-populating tsv_primary_blockchain_address')
    conn.execute(sa.sql.text('''UPDATE "user" u1 SET tsv_primary_blockchain_address = to_tsvector(u1.primary_blockchain_address);'''))

    print('Creating Triggers')
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_email_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_email, 'pg_catalog.simple', email);'''))
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_phone_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_phone, 'pg_catalog.simple', _phone);'''))
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_first_name_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_first_name, 'pg_catalog.simple', first_name);'''))
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_last_name_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_last_name, 'pg_catalog.simple', last_name);'''))
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_public_serial_number_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_public_serial_number, 'pg_catalog.simple', _public_serial_number);'''))
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_location_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_location, 'pg_catalog.simple', _location);'''))
    conn.execute(sa.sql.text('''CREATE TRIGGER tsv_primary_blockchain_address_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_primary_blockchain_address, 'pg_catalog.simple', primary_blockchain_address);'''))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_email_trigger on "user";'''))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_phone_trigger on "user";'''))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_first_name_trigger on "user";'''))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_last_name_trigger on "user";'''))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_public_serial_number_trigger on "user";'''))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_location_trigger on "user";'''))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS tsv_primary_blockchain_address_trigger on "user";'''))

    op.drop_column('user', 'tsv_public_serial_number')
    op.drop_column('user', 'tsv_primary_blockchain_address')
    op.drop_column('user', 'tsv_phone')
    op.drop_column('user', 'tsv_location')
    op.drop_column('user', 'tsv_last_name')
    op.drop_column('user', 'tsv_first_name')
    op.drop_column('user', 'tsv_email')
    op.drop_column('user', 'tsv_default_transfer_account_id')
