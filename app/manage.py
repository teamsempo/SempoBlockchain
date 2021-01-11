from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

from server import create_app, db
from migrations.seed import (
    create_ussd_menus,
    create_business_categories,
    create_float_transfer_account,
    create_reserve_token,
    create_master_organisation
)


class UpdateData(Command):

    def run(self):
        with app.app_context():

            create_ussd_menus()
            create_business_categories()
            reserve_token = create_reserve_token(app)
            create_master_organisation(app, reserve_token)
            create_float_transfer_account(app)


app = create_app()
manager = Manager(app)

migrate = Migrate(app, db, compare_type=True)

manager.add_command('db', MigrateCommand)

manager.add_command('update_data', UpdateData())


if __name__ == '__main__':
    manager.run()
