"""patch to add missing menu entry for ussd for account creation

Revision ID: 50837b220aba
Revises: 3500c08573ff
Create Date: 2020-05-02 15:16:38.260259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50837b220aba'
down_revision = '3500c08573ff'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.sql.text('insert into ussd_menu (name,description,display_key) values (\'exit_account_creation_prompt\', \'Successful account creation\', \'ussd.kenya.exit_account_creation_prompt\')'));
    pass


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.sql.text('delete from ussd_menu where name = \'exit_account_creation_prompt\''));
    pass
