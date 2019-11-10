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

            print("~~~~~~~~~~ Setting up Reserve Tokens and Contract ~~~~~~~~~~")

            from server.models.token import Token
            from server.models.exchange import ExchangeContract

            reserve_token_address = app.config.get('RESERVE_TOKEN_ADDRESS')
            exchange_contract_address = app.config.get('EXCHANGE_CONTRACT_ADDRESS')

            if reserve_token_address and exchange_contract_address:
                reserve_token = Token.query.filter_by(address=reserve_token_address).first()

                if not reserve_token:
                    reserve_token = Token(
                        address=reserve_token_address,
                        name='RESERVE_TOKEN',
                        symbol='RSRV'
                    )
                    db.session.add(reserve_token)
                    db.session.commit()

                exchange_contract = ExchangeContract.query.filter_by(
                    blockchain_address=exchange_contract_address).first()

                if not exchange_contract:
                    exchange_contract = ExchangeContract(blockchain_address=exchange_contract_address)

                    exchange_contract.reserve_token = reserve_token
                    exchange_contract.add_token(reserve_token)

                    db.session.add(exchange_contract)
                    db.session.commit()

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
