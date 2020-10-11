"""Add boolean to auto-approve externally created users 

Revision ID: f70402545b60
Revises: 17269ee60c54
Create Date: 2020-10-08 15:43:20.735649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f70402545b60'
down_revision = '17269ee60c54'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organisation', sa.Column('auto_approve_externally_created_users', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organisation', 'auto_approve_externally_created_users')
    # ### end Alembic commands ###
