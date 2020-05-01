"""Enforcing non nullable Organisation columns

Revision ID: 3500c08573ff
Revises: 0da0913f9dbd
Create Date: 2020-04-24 15:41:41.934453

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3500c08573ff'
down_revision = '0da0913f9dbd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("UPDATE organisation SET _country_code = 'AU' WHERE _country_code is NULL")
    op.alter_column('organisation', '_country_code',
                    existing_type=sa.VARCHAR(),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('organisation', '_country_code',
                    existing_type=sa.VARCHAR(),
                    nullable=True)
    # ### end Alembic commands ###
