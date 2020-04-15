import pytest, json
from faker.providers import phone_number
from faker import Faker

from server.utils.auth import get_complete_auth_token
from server.utils.phone import proccess_phone_number
from server.models.transfer_usage import TransferUsage

fake = Faker()
fake.add_provider(phone_number)


@pytest.mark.parametrize("user_phone_accessor, phone, business_usage_name, referred_by, tier, status_code", [
    (lambda o: o.phone, None, 'Fuel/Energy', '+61401391419', 'superadmin', 400),
    (lambda o: o.phone, fake.msisdn(), 'Fuel/Energy', fake.msisdn(), 'superadmin', 200),
    (lambda o: o.phone, fake.msisdn(), 'Food/Water', fake.msisdn(), 'view', 403)
])
def test_create_user(test_client, authed_sempo_admin_user, init_database, create_transfer_account_user, user_phone_accessor, phone,
                     business_usage_name, referred_by, tier, status_code):
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.post(
        "/api/v1/user/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'first_name': 'John',
            'last_name': 'Smith',
            'bio': 'EasyMart',
            'gender': 'female',
            'phone': phone,
            'is_vendor': False,
            'is_tokenagent': False,
            'is_groupaccount': False,
            'initial_disbursement': 0,
            'location': 'Elwood',
            'business_usage_name': business_usage_name,
            'referred_by': user_phone_accessor(create_transfer_account_user) #create the user who is referring
        })
    
    assert response.status_code == status_code
    if response.status_code == 200:
        data = response.json['data']
        assert isinstance(data['user'], object)
        assert data['user']['first_name'] == 'John'
        assert data['user']['last_name'] == 'Smith'
        assert data['user']['custom_attributes']['bio'] == 'EasyMart'
        assert data['user']['custom_attributes']['gender'] == 'female'
        assert data['user']['phone'] == proccess_phone_number(phone)
        assert data['user']['is_vendor'] is False
        assert data['user']['is_tokenagent'] is False
        assert data['user']['is_groupaccount'] is False
        assert data['user']['transfer_accounts'][0]['balance'] == 0
        assert data['user']['location'] == 'Elwood'
        assert data['user']['business_usage_id'] == init_database.session.query(TransferUsage)\
            .filter_by(name=business_usage_name).first().id
        # assert data['user']['referred_by'] == referred_by  #todo: not returned in schema, fixed in #PR123


@pytest.mark.parametrize("user_id_accessor, is_vendor, is_groupaccount, tier, status_code", [
    (lambda o: o.id, False, False, 'subadmin', 403),
    (lambda o: o.id, True, False, 'admin', 200),
    (lambda o: o.id, False, True, 'admin', 200),
    (lambda o: 1222103, False, False, 'admin', 400),
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


@pytest.mark.parametrize("user_id_accessor, tier, status_code", [
    (lambda o: o.id, 'admin', 403),
    (lambda o: o.id, 'superadmin', 200),
    (lambda o: o.id, 'superadmin', 400),
    (lambda o: 1222103, 'superadmin', 404),
])
def test_delete_user(test_client, authed_sempo_admin_user, create_transfer_account_user, user_id_accessor, tier,
                     status_code):
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.delete(
        f"/api/v1/user/{user_id_accessor(create_transfer_account_user)}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ))

    assert response.status_code == status_code
    if response.status_code == 200:
        assert response.json['message'] is not None
