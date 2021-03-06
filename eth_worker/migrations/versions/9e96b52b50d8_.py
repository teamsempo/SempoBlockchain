"""empty message

Revision ID: 9e96b52b50d8
Revises: 1eac1d8547a1
Create Date: 2019-09-16 10:23:06.064338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e96b52b50d8'
down_revision = '1eac1d8547a1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('blockchain_address', 'address',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.add_column('blockchain_task', sa.Column('gasLimit', sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('blockchain_task', 'gasLimit')
    op.alter_column('blockchain_address', 'address',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
