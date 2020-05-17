"""extended location information

Revision ID: 241af81119c4
Revises: fbc9b56af590
Create Date: 2020-04-23 11:37:45.838998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '241af81119c4'
down_revision = 'fbc9b56af590'
branch_labels = None
depends_on = None


location_external_source_options = ('OSM', 'GEONAMES')
location_external_source_enum = sa.Enum(*location_external_source_options, name='location_external_source_enum')

 
def upgrade():

    # hierarchically nested location resources
    op.create_table('location',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parent_id', sa.Integer()),
            sa.Column('common_name', sa.String(), nullable=False),
            sa.Column('latitude', sa.Numeric(), nullable=False),
            sa.Column('longitude', sa.Numeric(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
    )
   

    # links to external entities describing the same location resource
    op.create_table('location_external',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('location_id', sa.Integer(), nullable=False),
            sa.Column('source', location_external_source_enum, nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['location_id'], ['location.id'])
    )
    c = op.get_bind()
    c.execute("""ALTER TABLE location_external ADD COLUMN external_reference JSONB""")
    op.create_index('external_id_source_idx', 'location_external', ['source', 'external_reference'], schema=None, unique=True)

    # bind user to location, also preparing for improved modularization
    # and clean-up of user-related objects in db
    op.create_table('user_extension_association_table',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('location_id', sa.Integer()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['location_id'], ['location.id']),
    )
    op.create_index('user_extension_location_idx', 'user_extension_association_table', ['user_id', 'location_id'], schema=None, unique=True)


def downgrade():
    op.drop_index('user_extension_location_idx')
    op.drop_table('user_extension_association_table')
    op.drop_index('external_id_source_idx')
    op.drop_table('location_external')
    location_external_source_enum.drop(op.get_bind(), checkfirst=False)
    op.drop_table('location')
