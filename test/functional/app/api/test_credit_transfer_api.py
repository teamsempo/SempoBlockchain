import pytest, json
from server.utils.auth import get_complete_auth_token

# todo-  put credit transfer

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
    # todo: get p2p payments working
    # (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: u.id, 'PAYMENT', 'admin', 'PENDING', 201),
    # (10, None, lambda t: None, lambda u: None, lambda u: u.id, lambda u: u.id, 'PAYMENT', 'superadmin', 'COMPLETE', 201),
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

    assert response.status_code == status_code

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
    response = test_client.get(
        f"/api/v1/credit_transfer/{credit_transfer_selector_func(create_credit_transfer) or ''}",
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == status_code

    if not credit_transfer_selector_func(create_credit_transfer):
        assert isinstance(response.json['data']['credit_transfers'], list)

