from utils import address
from eth_src.sql_persistence.models import BlockchainTransaction

def test_process_send_eth_transaction(processor, db_session, dummy_transaction):

    txn_id = processor.process_send_eth_transaction(
        dummy_transaction.id, address, 123
    )

    txn = db_session.query(BlockchainTransaction).get(txn_id)



def test_proccess_deploy_contract_transaction(processor, dummy_transaction):

    processor.process_deploy_contract_transaction(
        dummy_transaction.id, 'ERC20Token', args=('FooToken', 'FTK', 18)
    )
#
# def test_proccess_deploy_contract_transaction(processor, dummy_transaction):
#
#     processor.process_deploy_contract_transaction(
#         dummy_transaction.id, 'ERC20Token', args=('FooToken', 'FTK', 18)
#     )