from flask import make_response, jsonify, g, copy_current_request_context
import threading

from server import db, bt
from server.models.token import Token, TokenType
from server.models.exchange import ExchangeContract
from server.models.organisation import Organisation


def deploy_cic_token(post_data, creating_org=None):
    name = post_data['name']
    symbol = post_data['symbol']
    decimals = post_data.get('decimals', 18)
    issue_amount_wei = int(post_data['issue_amount_wei'])
    reserve_deposit_wei = int(post_data['reserve_deposit_wei'])
    exchange_contract_id = post_data['exchange_contract_id']
    reserve_ratio_ppm = post_data.get('reserve_ratio_ppm', 250000)
    allow_autotopup = post_data.get('allow_autotopup', False)

    if creating_org:
        deploying_address = creating_org.primary_blockchain_address
    else:
        deploying_address = g.user.primary_blockchain_address

    if not exchange_contract_id:
        response_object = {
            'message': 'Must supply exchange contract id if deploying smart token contract'
        }

        return response_object, 400

    exchange_contract = ExchangeContract.query.get(exchange_contract_id)

    if not exchange_contract:
        response_object = {
            'message': 'Exchange contract not found for id {}'.format(exchange_contract_id)
        }

        return response_object, 400

    balance_wei = bt.get_wallet_balance(deploying_address, exchange_contract.reserve_token)

    if balance_wei < reserve_deposit_wei:

        if not allow_autotopup:
            response_object = {
                'message': f'Insufficient reserve funds (balance in wei: {balance_wei}). Please load the master wallet manually!'
            }

            return response_object, 400

        load_amount = int((reserve_deposit_wei - balance_wei) / 1e16)

        master_org = Organisation.master_organisation()

        print(f'Insufficient reserve funds (balance in wei: {balance_wei}), loading')

        if master_org.org_level_transfer_account.balance < load_amount:
            response_object = {
                'message': f'Insufficient reserve funds for both deploying account  ({balance_wei} wei), '
                           f'and master ({master_org.org_level_transfer_account.balance * 1e16} wei)'
            }

            return response_object, 400

        load_task_uuid = bt.make_token_transfer(
            signing_address=master_org.primary_blockchain_address,
            token=exchange_contract.reserve_token,
            from_address=master_org.primary_blockchain_address,
            to_address=deploying_address,
            amount=load_amount
        )

        try:
            bt.await_task_success(load_task_uuid)
        except TimeoutError:
            response_object = {
                'message': f'Insufficient reserve funds (balance in wei: {balance_wei}), and could not load from master'
            }

            return response_object, 400

        current_bal_offset = master_org.org_level_transfer_account.balance_offset
        master_org.org_level_transfer_account.set_balance_offset(current_bal_offset - load_amount)

    token = Token(name=name, symbol=symbol, token_type=TokenType.LIQUID)
    token.decimals = 18
    db.session.add(token)
    db.session.flush()

    deploy_data = dict(
        deploying_address=deploying_address,
        name=name, symbol=symbol, decimals=decimals,
        reserve_deposit_wei=reserve_deposit_wei,
        issue_amount_wei=issue_amount_wei,
        contract_registry_address=exchange_contract.contract_registry_blockchain_address,
        reserve_token_address=exchange_contract.reserve_token.address,
        reserve_ratio_ppm=reserve_ratio_ppm
    )

    @copy_current_request_context
    def deploy(_deploy_data, _token_id, _exchange_contract_id, _creating_org_id=None):
        smart_token_result = bt.deploy_smart_token(**_deploy_data)

        address = smart_token_result['smart_token_address']
        subexchange_address = smart_token_result['subexchange_address']

        _token = Token.query.get(_token_id)
        _token.address = address

        _exchange_contract = ExchangeContract.query.get(_exchange_contract_id)
        _exchange_contract.add_token(_token, subexchange_address, reserve_ratio_ppm)

        if _creating_org_id:

            _creating_org = Organisation.query.get(_creating_org_id)
            _creating_org.bind_token(_token)
            _creating_org.org_level_transfer_account.set_balance_offset(int(_deploy_data['issue_amount_wei'] / 1e16))

            bal = bt.get_wallet_balance(_creating_org.primary_blockchain_address, _token)

            print(f'Balance is {bal}')

        db.session.commit()

    if creating_org:
        creating_org_id = creating_org.id
    else:
        creating_org_id = None

    t = threading.Thread(target=deploy,
                         args=(deploy_data, token.id, exchange_contract_id, creating_org_id))
    t.daemon = True
    t.start()

    response_object = {
        'message': 'success',
        'data': {
            'token_id': token.id
        }
    }

    return response_object, 201

