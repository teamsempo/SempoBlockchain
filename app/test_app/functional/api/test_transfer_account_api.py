import pytest
from server.utils.auth import get_complete_auth_token
from server.models.transfer_account import TransferAccount
from server.utils.transfer_enums import TransferStatusEnum
from server import db
import random

@pytest.mark.parametrize("tier, initial_disbursement, is_approved, transfer_status, transfer_account_approver_tier, account_approval_http_status, final_transfer_status, final_is_approved", [   
    # Every relevant admin tier, at default disbursement amount 
    ('subadmin', 200, False, TransferStatusEnum.PENDING, 'subadmin', 403, TransferStatusEnum.PENDING, False),
    ('subadmin', 200, False, TransferStatusEnum.PENDING, 'admin', 201, TransferStatusEnum.COMPLETE, True),
    ('admin', 200, True, TransferStatusEnum.COMPLETE, 'admin', 201, TransferStatusEnum.COMPLETE, True),
    ('superadmin', 200, True, TransferStatusEnum.COMPLETE, 'admin', 201, TransferStatusEnum.COMPLETE, True),
    # Every relevant admin tier, exceeding default disbursement amount 
    ('subadmin', 800, False, TransferStatusEnum.PENDING, 'admin', 201, TransferStatusEnum.PENDING, True),
    ('admin', 800, True, TransferStatusEnum.PENDING, 'admin', 201, TransferStatusEnum.PENDING, True),
    ('superadmin', 800, True, TransferStatusEnum.COMPLETE, 'admin', 201, TransferStatusEnum.COMPLETE, True),
    ('subadmin', 800, False, TransferStatusEnum.PENDING, 'superadmin', 201, TransferStatusEnum.COMPLETE, True),
])
def test_disbursement_conditions(test_client, authed_sempo_admin_user, tier, initial_disbursement, is_approved, transfer_status, transfer_account_approver_tier, account_approval_http_status, final_transfer_status, final_is_approved):
    authed_sempo_admin_user.set_held_role('ADMIN', tier)
    auth = get_complete_auth_token(authed_sempo_admin_user)
    # Create user!
    payload = {
            'first_name': 'Francine',
            'last_name': 'Frensky',
            'gender': 'female',
            'phone': f'+1{random.randint(1000000000, 9999999999)}',
            'account_types': ['beneficiary'],
            'location': 'Elwood',
            'initial_disbursement': initial_disbursement,
        }
    response = test_client.post(
        "/api/v1/user/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json=payload)
    transfer_account_id = response.json['data']['user']['default_transfer_account_id']

    transfer_account = db.session.query(TransferAccount)\
        .filter(TransferAccount.id == transfer_account_id)\
        .first()
    
    assert transfer_account.is_approved == is_approved
    assert len(transfer_account.credit_receives) == 1
    disbursement = transfer_account.credit_receives[0]
    assert disbursement.is_initial_disbursement == True
    assert disbursement.transfer_status == transfer_status
    authed_sempo_admin_user.set_held_role('ADMIN', transfer_account_approver_tier)
    auth = get_complete_auth_token(authed_sempo_admin_user)

    response = test_client.put(
        f"/api/v1/transfer_account/{transfer_account_id}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'approve': True
        })

    assert response.status_code == account_approval_http_status
    if account_approval_http_status == 201:
        transfer_account = db.session.query(TransferAccount)\
            .filter(TransferAccount.id == transfer_account_id)\
            .first()

        assert len(transfer_account.credit_receives) == 1 # Make sure we don't get a double-disbursement on account approval
        disbursement = transfer_account.credit_receives[0]
        assert disbursement.transfer_status == final_transfer_status
    assert transfer_account.is_approved == final_is_approved
        
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
            'approve': True,
            'notes': 'This account has a comment!'
        })

    assert response.status_code == status_code
    if response.status_code == 201:
        assert response.json['data']['transfer_account'] is not None
        assert response.json['data']['transfer_account'][
                   'balance'] == 0
        assert response.json['data']['transfer_account']['notes'] == 'This account has a comment!'

@pytest.mark.parametrize("transfer_account_id_accessor, tier, status_code", [
    (lambda u: None, None, 401),
    (lambda u: u.transfer_account.id, 'subadmin', 403),
    (lambda u: u.transfer_account.id, 'superadmin', 201),  # todo(#320): this should be a 200 Status code
])
def test_put_multiple_transfer_account_api(test_client, authed_sempo_admin_user, create_transfer_account_user_function,
                                           transfer_account_id_accessor, tier, status_code):
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
                       'balance'] == 0
