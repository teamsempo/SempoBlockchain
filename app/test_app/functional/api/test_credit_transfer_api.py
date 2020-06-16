import pytest, json, base64, config
from server.utils.auth import get_complete_auth_token
from test_app.helpers.utils import assert_resp_status_code
from server.utils.user import create_transfer_account_user
from server.models.credit_transfer import CreditTransfer

@pytest.mark.parametrize("transfer_amount, target_balance, credit_transfer_uuid_selector_func, "
                         "recipient_transfer_accounts_ids_accessor, sender_user_id_accessor,"
                         "recipient_user_id_accessor,"
                         "transfer_type, tier, transfer_status, status_code", [
    (None, None, lambda t: None, lambda u: None, lambda u: None, lambda u: None, None, 'view', None, 403),
    (None, None, lambda t: None, lambda u: None, lambda u: None, lambda u: None, None, 'subadmin', None, 403),
    (None, None, lambda t: t.uuid, lambda u: None, lambda u: None, lambda u: None, None, 'admin', 'PENDING', 201),
    (0, None, lambda t: None, lambda u: None, lambda u: None, lambda u: None, None, 'admin', None, 400),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, None, 'admin', None, 400),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'PAYMENT', 'admin', None, 400),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: u.id, 'PAYMENT', 'admin', 'PENDING', 201),
    (
    10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: u.id, 'PAYMENT', 'superadmin', 'COMPLETE', 201),
    (None, 10, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'BALANCE', 'admin', 'PENDING', 201),
    (None, 10, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'BALANCE', 'superadmin', 'COMPLETE', 201),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'BALANCE', 'admin', None, 201),  # returns 400 in bulk
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'DISBURSEMENT', 'admin', 'PENDING', 201),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'DISBURSEMENT', 'superadmin', 'COMPLETE', 201),
    (-1, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'RECLAMATION', 'admin', None, 400),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'RECLAMATION', 'admin', None, 400),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: None, 'RECLAMATION', 'admin', 'PENDING', 201),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: None, 'RECLAMATION', 'superadmin', 'COMPLETE', 201),
])
def test_create_credit_transfer(test_client, authed_sempo_admin_user, create_transfer_account_user,
                                create_credit_transfer, transfer_amount, target_balance,
                                credit_transfer_uuid_selector_func, recipient_transfer_accounts_ids_accessor,
                                sender_user_id_accessor, recipient_user_id_accessor,
                                transfer_type, tier, transfer_status, status_code):

    recipient_transfer_accounts_ids = recipient_transfer_accounts_ids_accessor(create_transfer_account_user)
    if recipient_transfer_accounts_ids:
        recipient_transfer_accounts_ids = [recipient_transfer_accounts_ids]

    # Hack to prevent previous tests from causing future tests to fail
    # TODO: Change design of entire testing process to enable quick setup of blockchain etc, but not have tests so path dependent
    create_transfer_account_user.credit_sends = []
    create_transfer_account_user.credit_receives = []

    sender_user_id = sender_user_id_accessor(create_transfer_account_user)

    recipient_user_id = recipient_user_id_accessor(create_transfer_account_user)

    if transfer_type == 'PAYMENT' and sender_user_id:
        create_transfer_account_user.transfer_account.balance = 10000
        create_transfer_account_user.transfer_account.is_approved = True

    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.post(
        '/api/v1/credit_transfer/',
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        data=json.dumps(dict(
            transfer_amount=transfer_amount,
            target_balance=target_balance,
            uuid=credit_transfer_uuid_selector_func(create_credit_transfer),
            recipient_transfer_accounts_ids=recipient_transfer_accounts_ids,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            transfer_type=transfer_type
        )),
        content_type='application/json', follow_redirects=True)

    assert_resp_status_code(response, status_code)

    if response.status_code == 201:
        data = response.json['data']
        is_bulk = response.json.get('bulk_responses', None)

        if recipient_transfer_accounts_ids:
            if is_bulk[0].get('status', None) != status_code:
                print(is_bulk)
            else:
                assert data['credit_transfers'][0]['transfer_status'] == transfer_status
                assert isinstance(data['credit_transfers'], list)
        else:
            assert data['credit_transfer']['transfer_status'] == transfer_status
            assert isinstance(data['credit_transfer'], object)


@pytest.mark.parametrize("credit_transfer_selector_func, status_code", [
    (lambda o: o.id, 200),
    (lambda o: 1222103, 404),
    (lambda o: None, 200)
])
def test_get_credit_transfer(test_client, complete_admin_auth_token, create_credit_transfer,
                          credit_transfer_selector_func, status_code):
    if credit_transfer_selector_func(create_credit_transfer):
        url = f"/api/v1/credit_transfer/{credit_transfer_selector_func(create_credit_transfer)}/"
    else:
        url = '/api/v1/credit_transfer/'
    response = test_client.get(
        url,
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == status_code

    if not credit_transfer_selector_func(create_credit_transfer):
        assert isinstance(response.json['data']['credit_transfers'], list)


def test_credit_transfer_internal_callback(test_client, authed_sempo_admin_user, create_credit_transfer, create_organisation):
    # For this, we want to test 5 permutations of third-party transactions to add:
    # 1. Existing User A -> Existing User B
    # 2. Existing User A -> Stranger A
    # 3. Existing User A -> Stranger A (to ensure we don't give Stranger A two ghost accounts)
    # 4. Stranger B -> Existing User A
    # 5. Idempotency check (repeat step 4's request, ensure only one transfer is created)

    # Util function to POST to internal credit_transfer, since we'll be doing that a lot
    def post_to_credit_transfer_internal(sender_blockchain_address, recipient_blockchain_address, blockchain_transaction_hash, transfer_amount, contract_address):
        basic_auth = 'Basic ' + base64.b64encode(bytes(config.INTERNAL_AUTH_USERNAME + ":" + config.INTERNAL_AUTH_PASSWORD, 'ascii')).decode('ascii')
        return test_client.post(
            '/api/v1/credit_transfer/internal/',
            headers=dict(
                Authorization=basic_auth,
                Accept='application/json'
            ),
            data=json.dumps(dict(
                sender_blockchain_address=sender_blockchain_address,
                recipient_blockchain_address=recipient_blockchain_address,
                blockchain_transaction_hash=blockchain_transaction_hash,
                transfer_amount=transfer_amount,
                contract_address=contract_address,
            )),
            content_type='application/json', follow_redirects=True)


    org = create_organisation
    token = org.token

    # 1. Existing User A -> Existing User B
    existing_user_a = create_transfer_account_user(
                                    first_name='Arthur',
                                    last_name='Read',
                                    phone="+19025551234",
                                    organisation=org,
                                    initial_disbursement = 100)

    existing_user_b = create_transfer_account_user(
                                    first_name='Buster',
                                    last_name='Baxter',
                                    phone="+19025554321",
                                    organisation=org,
                                    initial_disbursement = 100)
    made_up_hash = '0xdeadbeef2322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'

    resp = post_to_credit_transfer_internal(existing_user_a.default_transfer_account.blockchain_address, existing_user_b.default_transfer_account.blockchain_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['sender_transfer_account']['id'] == existing_user_a.default_transfer_account.id
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] == existing_user_b.default_transfer_account.id
    

    transfer_id = resp.json['data']['credit_transfer']['id']

    transfer = CreditTransfer.query.filter_by(id=transfer_id).execution_options(show_all=True).first()
    assert transfer.sender_transfer_account == existing_user_a.default_transfer_account
    assert transfer.recipient_transfer_account == existing_user_b.default_transfer_account

    # 2. Existing User A -> Stranger A
    fake_user_a_address = '0xA9450d3dB5A909b08197BC4a0665A4d632539739'
    made_up_hash = '0x0000beef2322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'

    resp = post_to_credit_transfer_internal(existing_user_a.default_transfer_account.blockchain_address, fake_user_a_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['sender_transfer_account']['id'] == existing_user_a.default_transfer_account.id
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] != existing_user_b.default_transfer_account.id
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] != existing_user_a.default_transfer_account.id
    
    stranger_a_id = resp.json['data']['credit_transfer']['recipient_transfer_account']['id']

    transfer_id = resp.json['data']['credit_transfer']['id']
    transfer = CreditTransfer.query.filter_by(id=transfer_id).execution_options(show_all=True).first()

    assert transfer.sender_transfer_account == existing_user_a.default_transfer_account
    assert transfer.recipient_transfer_account.blockchain_address == fake_user_a_address

    # 3. Existing User A -> Stranger A (to ensure we don't give Stranger A two ghost accounts)
    made_up_hash = '0x000011112322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'

    resp = post_to_credit_transfer_internal(existing_user_a.default_transfer_account.blockchain_address, fake_user_a_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['sender_transfer_account']['id'] == existing_user_a.default_transfer_account.id
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] == stranger_a_id 
    
    transfer_id = resp.json['data']['credit_transfer']['id']
    transfer = CreditTransfer.query.filter_by(id=transfer_id).execution_options(show_all=True).first()

    assert transfer.sender_transfer_account == existing_user_a.default_transfer_account
    assert transfer.recipient_transfer_account.blockchain_address == fake_user_a_address

    # 4. Stranger B -> Existing User A
    fake_user_b_address = '0xA9450d3dB5A909b08197BC4a0665A4d632539739'
    made_up_hash = '0x2222beef2322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'

    resp = post_to_credit_transfer_internal(fake_user_b_address, existing_user_a.default_transfer_account.blockchain_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] == existing_user_a.default_transfer_account.id
    
    stranger_a_id = resp.json['data']['credit_transfer']['recipient_transfer_account']['id']

    transfer_id = resp.json['data']['credit_transfer']['id']
    transfer = CreditTransfer.query.filter_by(id=transfer_id).execution_options(show_all=True).first()

    assert transfer.recipient_transfer_account == existing_user_a.default_transfer_account
    assert transfer.sender_transfer_account.blockchain_address == fake_user_b_address

# 5. Idempotency check (repeat step 4's request, ensure only one transfer is created)
    resp_two = post_to_credit_transfer_internal(fake_user_b_address, existing_user_a.default_transfer_account.blockchain_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['id'] == resp_two.json['data']['credit_transfer']['id']
    #assert resp.json == resp_two.json