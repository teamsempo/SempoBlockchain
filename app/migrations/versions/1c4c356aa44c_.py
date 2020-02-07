"""empty message

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
index_set = [
    'tsv_email',
    'tsv_phone',
    'tsv_firstname',
    'tsv_lastname'
]
def upgrade():
    conn = op.get_bind()

    conn.execute(sa.sql.text('''
        CREATE MATERIALIZED VIEW search_view AS (
            SELECT
                u.email,
                u._phone,
                u.first_name,
                u.last_name,
                to_tsvector(u.email) AS tsv_email,
                to_tsvector(u._phone) AS tsv_phone,
                to_tsvector(u.first_name) AS tsv_first_name,
                to_tsvector(u.last_name) AS tsv_last_name,
            FROM user u
        )
    '''))


    op.create_index(op.f('ix_search_view_id'), 'search_view', ['id'], unique=True)

    op.create_index(op.f('ix_tsv_email'.format(index)), 'search_view', [index], postgresql_using='gin')
    op.create_index(op.f('ix_tsv_phone'.format(index)), 'search_view', [index], postgresql_using='gin')
    op.create_index(op.f('ix_tsv_firstname'.format(index)), 'search_view', [index], postgresql_using='gin')
    op.create_index(op.f('ix_tsv_lastname'.format(index)), 'search_view', [index], postgresql_using='gin')


def downgrade():
    pass
