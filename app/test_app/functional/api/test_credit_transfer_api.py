import pytest, json
from server.utils.auth import get_complete_auth_token
from test_app.helpers.utils import assert_resp_status_code
from server import db


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
        create_transfer_account_user.transfer_account.set_balance_offset(10000)
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


@pytest.mark.parametrize("is_bulk, invert_recipient_list, transfer_amount, transfer_type, status_code", [
    [True, False, 10, 'DISBURSEMENT', 201],
    [True, True, 20, 'DISBURSEMENT', 201]
])
def test_create_bulk_credit_transfer(test_client, authed_sempo_admin_user, create_transfer_account_user,
                                create_credit_transfer, is_bulk, invert_recipient_list, transfer_amount, 
                                transfer_type, status_code):
    from server.utils.user import create_transfer_account_user

    # Create admin user and auth
    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)

    # Create 15 users to test against
    users = []
    user_ids = []
    for _ in range(15):
        user = create_transfer_account_user(organisation=authed_sempo_admin_user.default_organisation)
        db.session.commit()
        users.append(user)
        user_ids.append(user.id)

    # Create set subset of created users to disburse to (first 5 users)
    recipients = user_ids[:5]

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
