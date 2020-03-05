"""empty message

Revision ID: 463ddd874cb8
Revises: fc2eeba8e8e8
Create Date: 2020-02-17 16:34:47.369834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '463ddd874cb8'
down_revision = 'fc2eeba8e8e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('kyc_application', 'postal_code',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('kyc_application', 'postal_code',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    # ### end Alembic commands ###
