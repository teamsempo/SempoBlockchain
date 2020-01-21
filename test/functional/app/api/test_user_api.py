import pytest, json
from faker.providers import phone_number
from faker import Faker

from server.utils.auth import get_complete_auth_token
from server.utils.phone import proccess_phone_number

fake = Faker()
fake.add_provider(phone_number)


@pytest.mark.parametrize("user_id_accessor, is_vendor, is_groupaccount, tier, status_code", [
    (lambda o: o.id, False, False, 'subadmin', 403),
    (lambda o: o.id, True, False, 'admin', 200),
    (lambda o: o.id, False, True, 'admin', 200),
    (lambda o: 1222103, False, False, 'admin', 404),
])
def test_edit_user(test_client, authed_sempo_admin_user, create_transfer_account_user, user_id_accessor, is_vendor, is_groupaccount, tier, status_code):
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    new_phone = fake.msisdn()

    response = test_client.put(
        f"/api/v1/user/{user_id_accessor(create_transfer_account_user)}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'phone': new_phone,
            'is_vendor': is_vendor,
            'is_groupaccount': is_groupaccount,
        })

    assert response.status_code == status_code
    if response.status_code == 200:
        data = response.json['data']

        assert isinstance(data['user'], object)
        assert data['user']['phone'] == proccess_phone_number(new_phone)
        assert data['user']['is_vendor'] == is_vendor
        assert data['user']['is_groupaccount'] == is_groupaccount


@pytest.mark.parametrize("reset_user_id_accessor,status_code", [
    (lambda u: 100, 404),
    (lambda u: None, 400),
    (lambda u: u.id, 200),
])
def test_admin_reset_user_pin(
        test_client, authed_sempo_admin_user, create_transfer_account_user, reset_user_id_accessor, status_code
):
    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)

    user_id = reset_user_id_accessor(create_transfer_account_user)
    response = test_client.post('/api/v1/user/reset_pin/',
                                headers=dict(Authorization=auth, Accept='application/json'),
                                data=json.dumps(dict(user_id=user_id)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
