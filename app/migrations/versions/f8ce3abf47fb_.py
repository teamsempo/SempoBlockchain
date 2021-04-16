"""Add require_multiple_transfer_approvals

Revision ID: f8ce3abf47fb
Revises: ea2d658b1695
Create Date: 2021-04-07 16:19:17.335393

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8ce3abf47fb'
down_revision = 'ea2d658b1695'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('credit_transfer_approver_user_association_table',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('credit_transfer_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['credit_transfer_id'], ['credit_transfer.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_index(op.f('ix_credit_transfer_approver_user_association_table_credit_transfer_id'), 'credit_transfer_approver_user_association_table', ['credit_transfer_id'], unique=False)
    op.create_index(op.f('ix_credit_transfer_approver_user_association_table_user_id'), 'credit_transfer_approver_user_association_table', ['user_id'], unique=False)
    op.add_column('organisation', sa.Column('require_multiple_transfer_approvals', sa.Boolean(), nullable=True))

    op.create_table('disbursement_approver_user_association_table',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('disbursement_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['disbursement_id'], ['disbursement.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_index(op.f('ix_disbursement_approver_user_association_table_disbursement_id'), 'disbursement_approver_user_association_table', ['disbursement_id'], unique=False)
    op.create_index(op.f('ix_disbursement_approver_user_association_table_user_id'), 'disbursement_approver_user_association_table', ['user_id'], unique=False)

    op.execute("ALTER TYPE transferstatusenum ADD VALUE IF NOT EXISTS 'PARTIAL'")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organisation', 'require_multiple_transfer_approvals')
    op.drop_index(op.f('ix_credit_transfer_approver_user_association_table_user_id'), table_name='credit_transfer_approver_user_association_table')
    op.drop_index(op.f('ix_credit_transfer_approver_user_association_table_credit_transfer_id'), table_name='credit_transfer_approver_user_association_table')
    op.drop_table('credit_transfer_approver_user_association_table')
    # ### end Alembic commands ###

    op.drop_table('disbursement_approver_user_association_table')
