from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

from server import create_app, db
from server.models.blockchain_address import BlockchainAddress
from server.models.transfer_account import TransferAccount, TransferAccountType

class UpdateData(Command):

    def run(self):
        with app.app_context():
            import config

            print("~~~~~~~~~~ Searching for Master Address ~~~~~~~~~~")

            master_address_type = "MASTER"
            master_address = app.config['MASTER_WALLET_ADDRESS']

            master_address_object = BlockchainAddress.query.filter(BlockchainAddress.type == master_address_type).first()

            if master_address_object is None:
                print('Creating Master Address')
                master_address_object = BlockchainAddress(type=master_address_type)
                master_address_object.address = master_address
                db.session.add(master_address_object)
                db.session.commit()

            elif master_address_object.address != master_address:
                print('Updating Master Address')

                master_address_object.address = master_address
                db.session.commit()

            print(master_address)

            # todo: [Nick] refactor this
            print("~~~~~~~~~~ Searching for float wallet ~~~~~~~~~~")

            float_wallet = TransferAccount.query.filter(TransferAccount.account_type == TransferAccountType.FLOAT).first()

            if float_wallet is None:
                print('Creating Float Wallet')
                float_wallet = TransferAccount(private_key=config.ETH_FLOAT_PRIVATE_KEY)
                db.session.add(float_wallet)
                db.session.commit()


app = create_app()
manager = Manager(app)

migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)

manager.add_command('update_data', UpdateData())


if __name__ == '__main__':
    manager.run()
