import pytest
from server.utils.auth import get_complete_auth_token
from server.models.user import User
from server import db
from sqlalchemy import func


@pytest.mark.parametrize("safety_check, balance, status_code", [
    (False, False, 400),
    (True, False, 400),  # insufficient balance
    (False, True, 400),  # No Safety Check
    (True, True, 200),
])
def test_mock_data(test_client, authed_sempo_admin_user, create_transfer_usage, safety_check, balance, status_code):
    users = db.session.query(func.count(User.id)).scalar()
    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)
    authed_sempo_admin_user.transfer_accounts.append(
        authed_sempo_admin_user.default_organisation.org_level_transfer_account) if len(
        authed_sempo_admin_user.transfer_accounts) == 0 else None
    authed_sempo_admin_user.default_organisation.org_level_transfer_account.set_balance_offset(10000) if balance \
        else None
    db.session.commit()

    response = test_client.post(
        '/api/v1/mock_data/',
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'number_of_users': 1,
            'number_of_transfers': 12,
            'number_of_days': 2,
            'safety_check': users if safety_check else None,
        })

    assert response.status_code == status_code
