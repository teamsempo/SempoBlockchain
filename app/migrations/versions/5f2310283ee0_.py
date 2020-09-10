"""
Adding attribute map table
Revision ID: 5f2310283ee0
Revises: 2c3f97929457
Create Date: 2020-09-04 18:57:09.532460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f2310283ee0'
down_revision = '2c3f97929457'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('attribute_map',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('authorising_user_id', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('input_name', sa.String(), nullable=False),
    sa.Column('output_name', sa.String(), nullable=False),
    sa.Column('organisation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('settings', sa.Column('is_public', sa.Boolean(), nullable=True))
    op.add_column('settings', sa.Column('organisation_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'settings', 'organisation', ['organisation_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'settings', type_='foreignkey')
    op.drop_column('settings', 'organisation_id')
    op.drop_column('settings', 'is_public')
    op.drop_table('attribute_map')
    # ### end Alembic commands ###