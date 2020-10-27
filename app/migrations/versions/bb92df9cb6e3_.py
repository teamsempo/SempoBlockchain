"""Adds unstarted value, and converts when we need to

Revision ID: bb92df9cb6e3
Revises: 2f8c71039480
Create Date: 2020-10-20 15:42:49.835818

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = 'bb92df9cb6e3'
down_revision = '2f8c71039480'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    session = Session(bind=conn)
    op.execute("COMMIT")
    op.execute("ALTER TYPE blockchainstatus ADD VALUE  IF NOT EXISTS 'UNSTARTED'")
    session.commit()
    op.execute("update credit_transfer set blockchain_status = 'UNSTARTED' where transfer_status = 'REJECTED';")

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
