"""empty message

Revision ID: 2be22b2cff07
Revises: cd5cb44c8f7c
Create Date: 2019-10-10 14:19:16.148945

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2be22b2cff07'
down_revision = 'cd5cb44c8f7c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('uploaded_resource',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('authorising_user_id', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('file_type', sa.String(), nullable=True),
    sa.Column('user_filename', sa.String(), nullable=True),
    sa.Column('reference', sa.String(), nullable=True),
    sa.Column('credit_transfer_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('kyc_application_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['credit_transfer_id'], ['credit_transfer.id'], ),
    sa.ForeignKeyConstraint(['kyc_application_id'], ['kyc_application.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('uploaded_document')
    op.drop_table('uploaded_image')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('uploaded_image',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('authorising_user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('credit_transfer_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('image_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['credit_transfer_id'], ['credit_transfer.id'], name='uploaded_image_credit_transfer_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='uploaded_image_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='uploaded_image_pkey')
    )
    op.create_table('uploaded_document',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('authorising_user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('file_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_filename', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reference', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('kyc_application_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['kyc_application_id'], ['kyc_application.id'], name='uploaded_document_kyc_application_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='uploaded_document_pkey')
    )
    op.drop_table('uploaded_resource')
    # ### end Alembic commands ###
