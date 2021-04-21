import pytest, json, base64, config
from server.utils.auth import get_complete_auth_token
from test_app.helpers.utils import assert_resp_status_code
from server.utils.user import create_transfer_account_user
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccountType
from server.models.organisation import Organisation
from server.models.transfer_card import TransferCard

from helpers.utils import will_func_test_blockchain
from server import bt, db

@pytest.mark.parametrize("transfer_amount, target_balance, credit_transfer_uuid_selector_func, "
                         "recipient_transfer_accounts_ids_accessor, sender_user_id_accessor,"
                         "recipient_user_id_accessor,"
                         "transfer_type, tier, transfer_status, invert_recipient_list, status_code", [
    (None, None, lambda t: None, lambda u: None, lambda u: None, lambda u: None, None, 'view', None, False, 403),
    (None, None, lambda t: None, lambda u: None, lambda u: None, lambda u: None, None, 'subadmin', None, False,  403),
    (None, None, lambda t: t.uuid, lambda u: None, lambda u: None, lambda u: None, None, 'admin', 'PENDING', False,  201),
    (0, None, lambda t: None, lambda u: None, lambda u: None, lambda u: None, None, 'admin', None, False, 400),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, None, 'admin', None, False, 400),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'PAYMENT', 'admin', None, False, 400),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: u.id, 'PAYMENT', 'admin', 'PENDING', False, 201),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: u.id, 'PAYMENT', 'superadmin', 'COMPLETE', False, 201),
    (None, 10, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'BALANCE', 'admin', 'PENDING', False, 201),
    (None, 10, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'BALANCE', 'superadmin', 'COMPLETE', False, 201),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'BALANCE', 'admin', None, False, 201),  # returns 400 in bulk
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'DISBURSEMENT', 'admin', 'PENDING', False, 201),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'DISBURSEMENT', 'superadmin', 'COMPLETE', False, 201),
    (-1, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'RECLAMATION', 'admin', None, False, 400),
    (10, None, lambda t: None, lambda u: u.id, lambda u: None, lambda u: None, 'RECLAMATION', 'admin', None, False, 400),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: None, 'RECLAMATION', 'admin', 'PENDING', False, 201),
    (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: None, 'RECLAMATION', 'superadmin', 'COMPLETE', True, 201),
])
def test_create_credit_transfer(test_client, authed_sempo_admin_user, create_transfer_account_user,
                                create_credit_transfer, transfer_amount, target_balance,
                                credit_transfer_uuid_selector_func, recipient_transfer_accounts_ids_accessor,
                                sender_user_id_accessor, recipient_user_id_accessor,
                                transfer_type, tier, transfer_status ,invert_recipient_list, status_code):

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
        create_transfer_account_user.transfer_account.set_balance_offset(1000000)
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
            transfer_type=transfer_type,
            invert_recipient_list=invert_recipient_list
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


def test_transfer_card_credit_transfer(test_client, complete_admin_auth_token, create_transfer_account_user):
    create_transfer_account_user.transfer_account.set_balance_offset(1000000)
    create_transfer_account_user.transfer_account.is_approved = True

    create_card = test_client.post(
        '/api/v1/transfer_cards/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'public_serial_number': '234432',
            'nfc_serial_number': 'DEADBEEF013223232'
        },
        content_type='application/json',
        follow_redirects=True
    )

    bind_user = test_client.put(
        f"/api/v1/user/{create_transfer_account_user.id}/",
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'public_serial_number': '234432'
        })

    response = test_client.post(
        '/api/v1/credit_transfer/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            "recipient_user_id": create_transfer_account_user.id,
            "sender_public_identifier": '234432',
            "transfer_amount": 10,
            "transfer_type": "PAYMENT"
        }
    )

    transfer_card = TransferCard.query.filter_by(public_serial_number='234432').first()

    assert response.json['data']['credit_transfer']['sender_transfer_card_id'] == transfer_card.id


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


def test_credit_transfer_internal_callback(mocker, test_client, authed_sempo_admin_user, create_organisation, new_credit_transfer):
    # For this, we want to test 5 permutations of third-party transactions to add:
    # 1. Existing User A -> Existing User B
    # 2. Existing User A -> Stranger A
    # 3. Existing User A -> Stranger A (to ensure we don't give Stranger A two ghost accounts)
    # 4. Stranger B -> Existing User A
    # 5. Idempotency check (repeat step 4's request, ensure only one transfer is created)
    # 6. Stranger A -> Stranger B To ensure we're not tracking transactions between strangers who are in the system
    # (Do nothing-- we don't care about transfers between strangers who aren't members)
    # 7. Stranger C -> Stranger D To ensure we're not tracking transactions between strangers who are NOT in the system
    # (Do nothing-- we don't care about transfers between strangers who aren't members)
    # 8. Existing Credit Transfer. 200 response, and received_third_party_sync becomes True 
    send_to_worker_called = []
    def mock_send_blockchain_payload_to_worker(is_retry=False, queue='high_priority'):
        send_to_worker_called.append([is_retry, queue])

    mocker.patch(
        'server.models.credit_transfer.CreditTransfer.send_blockchain_payload_to_worker',
        mock_send_blockchain_payload_to_worker
    )

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

    existing_user_a.default_transfer_account.set_balance_offset(1000)

    existing_user_b = create_transfer_account_user(
                                    first_name='Buster',
                                    last_name='Baxter',
                                    phone="+19025554321",
                                    organisation=org,
                                    initial_disbursement = 100)

    existing_user_b.default_transfer_account.set_balance_offset(1000)

    made_up_hash = '0xdeadbeef2322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'

    resp = post_to_credit_transfer_internal(existing_user_a.default_transfer_account.blockchain_address, existing_user_b.default_transfer_account.blockchain_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['sender_transfer_account']['id'] == existing_user_a.default_transfer_account.id
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] == existing_user_b.default_transfer_account.id
    
    transfer_id = resp.json['data']['credit_transfer']['id']

    transfer = CreditTransfer.query.filter_by(id=transfer_id).execution_options(show_all=True).first()
    assert transfer.sender_transfer_account == existing_user_a.default_transfer_account
    assert transfer.recipient_transfer_account == existing_user_b.default_transfer_account
    # Check that the user is being attached too
    assert transfer.sender_user_id == existing_user_a.id
    assert transfer.recipient_user_id == existing_user_b.id

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
    assert transfer.recipient_transfer_account.account_type == TransferAccountType.EXTERNAL
    assert transfer.sender_user_id == existing_user_a.id

    # Check that a blockchain task isn't created for outside transactions 
    assert transfer.blockchain_task_uuid == None
    # Check that a transfer made through TX sync can't be resolved as completed
    with pytest.raises(Exception):
        transfer.resolve_as_complete()


    # 3. Existing User A -> Stranger A (to ensure we don't give Stranger A two ghost accounts)
    made_up_hash = '0x000011112322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'

    resp = post_to_credit_transfer_internal(existing_user_a.default_transfer_account.blockchain_address, fake_user_a_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['sender_transfer_account']['id'] == existing_user_a.default_transfer_account.id
    assert resp.json['data']['credit_transfer']['recipient_transfer_account']['id'] == stranger_a_id 
    
    transfer_id = resp.json['data']['credit_transfer']['id']
    transfer = CreditTransfer.query.filter_by(id=transfer_id).execution_options(show_all=True).first()

    assert transfer.sender_transfer_account == existing_user_a.default_transfer_account
    assert transfer.recipient_transfer_account.blockchain_address == fake_user_a_address
    assert transfer.recipient_transfer_account.account_type == TransferAccountType.EXTERNAL
    assert transfer.sender_user_id == existing_user_a.id

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
    assert transfer.sender_transfer_account.account_type == TransferAccountType.EXTERNAL

    # 5. Idempotency check (repeat step 4's request, ensure only one transfer is created)
    resp_two = post_to_credit_transfer_internal(fake_user_b_address, existing_user_a.default_transfer_account.blockchain_address, made_up_hash, 100, token.address)
    assert resp.json['data']['credit_transfer']['id'] == resp_two.json['data']['credit_transfer']['id']

    # 6. Stranger B -> Stranger A (Strangers who exist in the system)
    made_up_hash = '0x2222b33f1322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb'
    resp = post_to_credit_transfer_internal(fake_user_b_address, fake_user_a_address, made_up_hash, 100, token.address)
    assert resp.json['message'] == 'Only external users involved in this transfer'

    # 7. Stranger C -> Stranger D (Strangers who do NOT exist in the system)
    made_up_hash = '0x2222b33f13288396649ed2fa2b7e0a944123b65cfab2c4b1435c81bb16697ecb'
    fake_user_c_address = '0xA9450d3dB5A909b08197BC4a0665A4d632539111'
    fake_user_d_address = '0xA9450d3dB5A909b08197BC4a0665A4d632539222'
    resp = post_to_credit_transfer_internal(fake_user_c_address, fake_user_d_address, made_up_hash, 100, token.address)
    assert resp.json['message'] == 'No existing users involved in this transfer'

    # 8. Stranger A -> Stranger E (One existing stanger, one new stranger)
    made_up_hash = '0x2222b33f13288396649ed2fffb7e0a944123b65cfab2c4b1435c81bb16697ecb'
    fake_user_e_address = '0xA9450d3dB5A909b08197BC4a0665A4d63253aaaf'
    resp = post_to_credit_transfer_internal(fake_user_a_address, fake_user_e_address, made_up_hash, 100, token.address)
    assert resp.json['message'] == 'Only external users involved in this transfer'

    # 9. Stranger E -> Stranger A (One new stranger, one existing stanger)
    made_up_hash = '0x2222b33f13288396649ed2fffb7e0a944123b65cfab2c4b1435c81bb12697ecb'
    fake_user_e_address = '0xA9450d3dB5A909b08197BC4a0665A4d63253aaaf'
    resp = post_to_credit_transfer_internal(fake_user_e_address, fake_user_a_address, made_up_hash, 100, token.address)
    assert resp.json['message'] == 'Only external users involved in this transfer'

    # Make sure we're not sending any of the tranfers off to the blockchain
    assert len(send_to_worker_called) == 0
    from flask import g
    assert len(g.pending_transactions) == 0

def test_force_third_party_transaction_sync():
    if will_func_test_blockchain():
        task_uuid = bt.force_third_party_transaction_sync()
        bt.await_task_success(task_uuid, timeout=config.CHAINS['ETHEREUM']['SYNCRONOUS_TASK_TIMEOUT'] * 48)

@pytest.mark.parametrize("is_bulk, invert_recipient_list, transfer_amount, transfer_type, status_code", [
    [True, False, 1000, 'DISBURSEMENT', 201],
    [True, True, 2000, 'DISBURSEMENT', 201]
])
def test_create_bulk_credit_transfer(test_client, authed_sempo_admin_user, create_transfer_account_user,
                                create_credit_transfer, is_bulk, invert_recipient_list, transfer_amount, 
                                transfer_type, status_code):
    from server.utils.user import create_transfer_account_user
    from flask import g

    # Create admin user and auth
    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)
    g.active_organisation = authed_sempo_admin_user.default_organisation
    # Create 15 users to test against
    users = []
    user_ids = []
    for _ in range(15):
        user = create_transfer_account_user(organisation=authed_sempo_admin_user.default_organisation)
        db.session.commit()
        users.append(user)
        user_ids.append(user.id)

    # Create set subset of created users to disburse to (first 5 users)
    recipients = [10, 11, 12, 13]
    
    response = test_client.post(
        '/api/v1/credit_transfer/',
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        data=json.dumps(dict(
            is_bulk=is_bulk,
            recipient_transfer_accounts_ids=recipients,
            invert_recipient_list=invert_recipient_list,
            transfer_amount=transfer_amount,
            transfer_type=transfer_type,
        )),
        content_type='application/json', follow_redirects=True)
    db.session.commit()

    # Get IDs for every user disbursed to, then check that the list matches up
    # with the list of recipients (or the inverse if invert_recipient_list)
    rx_ids = []
    for transfer in response.json['data']['credit_transfers']:
        rx_ids.append(transfer['recipient_transfer_account']['id'])
    if invert_recipient_list:
        for id in rx_ids:
            assert id not in recipients
    else: 
        assert rx_ids == recipients

@pytest.mark.parametrize("query_organisations, status_code", [
    ('', 200),
    ('1', 200),
    ('2', 200),
    ('1, 2', 200)
])
def test_credit_transfer_organisation_filters(test_client, init_database, authed_sempo_admin_user,
                                              complete_admin_auth_token, create_credit_transfer,
                                              query_organisations, status_code):
    # Checks that the credit_transfer endpoint supports multiple organisations
    url = f'/api/v1/credit_transfer/?query_organisations={query_organisations}'

    from server.models.organisation import Organisation
    # master_organisation is organisation 1
    master_organisation = Organisation.master_organisation()
    create_credit_transfer.sender_user.organisation = master_organisation
    create_credit_transfer.recipient_user.organisation = master_organisation
    create_credit_transfer.sender_transfer_account.organisation = master_organisation
    create_credit_transfer.recipient_transfer_account.organisation = master_organisation
    init_database.session.commit()

    # Add master_organisation (organisation 1) to our user's organisations. admin_user already
    # is a member of organisation 2
    authed_sempo_admin_user.organisations.append(master_organisation)

    response = test_client.get(
        url,
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    all_transfers = CreditTransfer.query.execution_options(show_all=True).all()

    org1 = Organisation.query.get(1)
    org2 = Organisation.query.get(2)

    org1_transfer_ids = set(t.id for t in all_transfers if org1 in t.organisations)
    org2_transfer_ids = set(t.id for t in all_transfers if org2 in t.organisations)

    assert response.status_code == status_code
    if status_code == 200:
        response_ids = set()
        for r in response.json['data'].get('credit_transfers', []):
            response_ids.add(r['id'])
        if '1' in query_organisations:
            assert create_credit_transfer.id in response_ids

        if query_organisations == '1':
            assert response_ids == org1_transfer_ids
        if query_organisations == '2' or query_organisations == '':
            assert response_ids == org2_transfer_ids
        if query_organisations == '1,2':
            assert response_ids == org1_transfer_ids.union(org2_transfer_ids)
