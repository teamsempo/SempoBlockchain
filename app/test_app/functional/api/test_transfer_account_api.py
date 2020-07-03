import pytest
from server.utils.auth import get_complete_auth_token


@pytest.mark.parametrize("transfer_account_id_accessor, tier, status_code", [
    (lambda u: u.transfer_account.id, None, 401),
    (lambda u: u.transfer_account.id, 'superadmin', 201),  # todo(#320): this should be a 200 Status code
    (lambda u: u.transfer_account.id, 'view', 201),  # todo(#320): this should be a 200 Status code
    (lambda o: 1222103, 'superadmin', 400),  # todo(#320): this should be a 404 Status code
])
def test_get_single_transfer_account_api(test_client, authed_sempo_admin_user, create_transfer_account_user_function,
                                         transfer_account_id_accessor, tier, status_code):
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.get(
        f"/api/v1/transfer_account/{transfer_account_id_accessor(create_transfer_account_user_function)}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ))

    assert response.status_code == status_code
    if response.status_code == 201:
        assert response.json['data']['transfer_account'] is not None


@pytest.mark.parametrize("account_type, tier, status_code", [
    (None, None, 401),
    ('vendor', 'superadmin', 200),
    ('beneficiary', 'view', 200),
])
def test_get_multiple_transfer_account_api(test_client, authed_sempo_admin_user, create_transfer_account_user_function,
                                           account_type, tier, status_code):
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.get(
        f"/api/v1/transfer_account/?account_type={account_type}",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ))

    assert response.status_code == status_code
    if response.status_code == 201:
        assert response.json['data']['transfer_accounts'] is not None


@pytest.mark.parametrize("transfer_account_id_accessor, tier, status_code", [
    (lambda u: u.transfer_account.id, None, 401),
    (lambda u: u.transfer_account.id, 'subadmin', 403),
    (lambda u: u.transfer_account.id, 'superadmin', 201),  # todo(#320): this should be a 200 Status code
    (lambda o: 1222103, 'superadmin', 400),  # todo(#320): this should be a 404 Status code
])
def test_put_single_transfer_account_api(test_client, authed_sempo_admin_user, create_transfer_account_user_function,
                                         transfer_account_id_accessor, tier, status_code):
    create_transfer_account_user_function.transfer_account.is_beneficiary = True
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.put(
        f"/api/v1/transfer_account/{transfer_account_id_accessor(create_transfer_account_user_function)}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'transfer_account_name': 'Acme Mart',
            'payable_period_type': 'weekly',
            'payable_period_length': '1',
            'payable_epoch': '2/7/20',
            'approve': True
        })

    assert response.status_code == status_code
    if response.status_code == 201:
        assert response.json['data']['transfer_account'] is not None
        assert response.json['data']['transfer_account'][
                   'balance'] == create_transfer_account_user_function.default_organisation.default_disbursement


@pytest.mark.parametrize("transfer_account_id_accessor, tier, status_code", [
    (lambda u: None, None, 401),
    (lambda u: u.transfer_account.id, 'subadmin', 403),
    (lambda u: u.transfer_account.id, 'superadmin', 201),  # todo(#320): this should be a 200 Status code
])
def test_put_multiple_transfer_account_api(test_client, authed_sempo_admin_user, create_transfer_account_user_function,
                                           transfer_account_id_accessor, tier, status_code):
    create_transfer_account_user_function.transfer_account.balance = 0
    create_transfer_account_user_function.transfer_account.is_beneficiary = True
    create_transfer_account_user_function.transfer_account.is_approved = False
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.put(
        f"/api/v1/transfer_account/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'transfer_account_id_list': [transfer_account_id_accessor(create_transfer_account_user_function)],
            'approve': True
        })

    assert response.status_code == status_code
    if response.status_code == 201:
        assert response.json['data']['transfer_accounts'] is not None
        if transfer_account_id_accessor(create_transfer_account_user_function) == 123123:
            # This user shouldn't exist
            assert response.json['data']['transfer_accounts'][0][
                       'status'] == 400  # todo(#320): this should be a 404 Status code
        else:
            assert response.json['data']['transfer_accounts'][0][
                       'balance'] == create_transfer_account_user_function.default_organisation.default_disbursement
