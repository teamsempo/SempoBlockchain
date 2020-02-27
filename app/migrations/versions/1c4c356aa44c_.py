"""Adds search_view with indexes

Revision ID: 1c4c356aa44c
Revises: fc2eeba8e8e8
Create Date: 2020-02-07 15:38:07.298134

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c4c356aa44c'
down_revision = 'fc2eeba8e8e8'
branch_labels = None
depends_on = None

trigger_tuples = [
    #user table
    ('user', 'email'),
    ('user', '_phone'),
    ('user', 'first_name'),
    ('user', 'last_name'),
]

def upgrade():
    conn = op.get_bind()

    conn.execute(sa.sql.text('''
        CREATE MATERIALIZED VIEW search_view AS (
            SELECT
                u.id,
                u.email,
                u._phone,
                u.first_name,
                u.last_name,
                u._public_serial_number,
                u._location,
                u.primary_blockchain_address,
                u.default_transfer_account_id,
                to_tsvector(u.email) AS tsv_email,
                to_tsvector(u._phone) AS tsv_phone,
                to_tsvector(u.first_name) AS tsv_first_name,
                to_tsvector(u.last_name) AS tsv_last_name,
                to_tsvector(u._public_serial_number) AS tsv_public_serial_number,
                to_tsvector(u._location) AS tsv_location,
                to_tsvector(u.primary_blockchain_address) AS tsv_primary_blockchain_address,
                to_tsvector(CAST (u.default_transfer_account_id AS VARCHAR(10))) AS tsv_default_transfer_account_id
            FROM "user" u
        );
    '''))

    op.create_index(op.f('ix_search_view_id'), 'search_view', ['id'], unique=True)
    op.create_index(op.f('ix_tsv_email'), 'search_view', ['tsv_email'], postgresql_using='gin')
    op.create_index(op.f('ix_tsv_phone'), 'search_view', ['tsv_phone'], postgresql_using='gin')
    op.create_index(op.f('ix_tsv_firstname'), 'search_view', ['tsv_first_name'], postgresql_using='gin')
    op.create_index(op.f('ix_tsv_lastname'), 'search_view', ['tsv_last_name'], postgresql_using='gin')
    op.create_index(op.f('_public_serial_number'), 'search_view', ['tsv_public_serial_number'], postgresql_using='gin')
    op.create_index(op.f('_location'), 'search_view', ['tsv_location'], postgresql_using='gin')
    op.create_index(op.f('primary_blockchain_address'), 'search_view', ['tsv_primary_blockchain_address'], postgresql_using='gin')
    op.create_index(op.f('default_transfer_account_id'), 'search_view', ['tsv_default_transfer_account_id'], postgresql_using='gin')

    # Function to refresh index
    conn.execute(sa.sql.text('''
        CREATE OR REPLACE FUNCTION trig_refresh_search_view() RETURNS trigger AS
        $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY search_view;
            RETURN NULL;
        END;
        $$
        LANGUAGE plpgsql ;
    '''))

    # Make the index update itself when users are changed (using above function)
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS search_trigger ON "user"'''))
    conn.execute(sa.sql.text('''
            CREATE TRIGGER search_trigger AFTER TRUNCATE OR INSERT OR DELETE OR UPDATE
            ON "user" FOR EACH STATEMENT
            EXECUTE PROCEDURE trig_refresh_search_view()
        '''))
            
def downgrade():
    conn = op.get_bind()
    # drop the materialized view and old trigger
    conn.execute(sa.sql.text('DROP MATERIALIZED VIEW search_view'))
    conn.execute(sa.sql.text('''DROP TRIGGER IF EXISTS search_trigger ON "user"'''))
