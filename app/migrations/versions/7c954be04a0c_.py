"""Add initial_disbursement_amount and sign_up_method

Revision ID: 7c954be04a0c
Revises: 463ddd874cb8
Create Date: 2020-02-21 15:35:34.167286

"""
from alembic import op
import sqlalchemy as sa
import psycopg2

# revision identifiers, used by Alembic.
revision = '7c954be04a0c'
down_revision = '463ddd874cb8'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('organisation', sa.Column('initial_disbursement_amount', sa.Float(precision=2), nullable=True))
        op.add_column('user', sa.Column('sign_up_method', sa.String(), nullable=True))
    except Exception as e:
        if 'relation "organisation" already exists' in repr(e):
            print('Relation already exists. Continuing.')
            pass

def downgrade():
    op.drop_column('organisation', 'initial_disbursement_amount')
    op.drop_column('user', 'sign_up_method')
