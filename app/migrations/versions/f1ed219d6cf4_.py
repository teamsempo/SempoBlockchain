"""Start using the custom_attribute table

Revision ID: f1ed219d6cf4
Revises: 917051c561c8
Create Date: 2020-09-04 12:13:18.518145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1ed219d6cf4'
down_revision = '917051c561c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('custom_attribute_user_storage', sa.Column('custom_attribute_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'custom_attribute_user_storage', 'custom_attribute', ['custom_attribute_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    op.drop_column('custom_attribute_user_storage', 'custom_attribute_id')
