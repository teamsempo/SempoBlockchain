import pytest, json, time
from faker.providers import phone_number
from faker import Faker
from random import randint
import base64



from server import db
from server.utils.auth import get_complete_auth_token
from server.utils.phone import proccess_phone_number
from server.utils.transfer_enums import TransferStatusEnum
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.models.transfer_card import TransferCard
from server.models.organisation import Organisation
from server.utils.user import create_transfer_account_user

fake = Faker()
fake.add_provider(phone_number)


@pytest.fixture(scope='function')
def mock_async_set_user_gps_from_location(mocker):
    fn_inputs = []

    class Mock:

        @staticmethod
        def submit(*args, **kwargs):
            fn_inputs.append([args, kwargs])

    mocker.patch('server.utils.location.async_set_user_gps_from_location', Mock)

    return fn_inputs


@pytest.mark.parametrize("user_phone_accessor, phone, use_card, business_usage_name, gps_location, referred_by, "
                         "initial_disbursement, tier, status_code",
                         [
                             (lambda o: o.phone, None, False, 'Fuel/Energy', None, '+61401391419', None, 'superadmin', 400),
                             (lambda o: o.phone, None, True, 'Fuel/Energy', '12.02 -15.04 otheruselessdata!##', '+61401391419', None, 'superadmin', 200),
                             (lambda o: o.phone, fake.msisdn(), False, 'Fuel/Energy', None, fake.msisdn(), 0, 'superadmin', 200),
                             (lambda o: o.phone, fake.msisdn(), False, 'Fuel/Energy', None, fake.msisdn(), None, 'superadmin', 200),
                             (lambda o: o.phone, fake.msisdn(), False, 'Food/Water', None, fake.msisdn(), None, 'view', 403)
                         ])
def test_create_user(test_client, authed_sempo_admin_user, init_database, create_transfer_account_user,
                     mock_async_set_user_gps_from_location, user_phone_accessor, phone, use_card,
                     business_usage_name, referred_by, gps_location, initial_disbursement, tier, status_code):

    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    # create the user who is referring
    create_transfer_account_user.phone = referred_by
    user_phone_accessor(create_transfer_account_user)

    payload = {
            'first_name': 'John',
            'last_name': 'Smith',
            'bio': 'EasyMart',
            'gender': 'female',
            'phone': phone,
            'initial_disbursement': initial_disbursement,
            'location': 'Elwood',
            'business_usage_name': business_usage_name,
            'referred_by': user_phone_accessor(create_transfer_account_user)
        }

    if gps_location:
        payload['gps_location'] = gps_location

    if use_card:
        public_serial_number = f'{randint(0,999999):06}'
        new_card = TransferCard(public_serial_number=public_serial_number)

        init_database.session.add(new_card)

        init_database.session.commit()

        payload['public_serial_number'] = public_serial_number

    response = test_client.post(
        "/api/v1/user/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json=payload)
    
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
        assert data['user']['location'] == 'Elwood'
        assert data['user']['business_usage_id'] == init_database.session.query(TransferUsage)\
            .filter_by(name=business_usage_name).first().id
        assert data['user']['referred_by'] == user_phone_accessor(create_transfer_account_user)

        if initial_disbursement is not None:
            assert data['user']['transfer_accounts'][0]['balance'] == initial_disbursement
        else:
            db_user = init_database.session.query(User).get(data['user']['id'])
            assert data['user']['transfer_accounts'][0]['balance'] == db_user.default_organisation.default_disbursement

        # Checks that we're calling the gps location fetching job, and passing the right data to it
        fn_inputs = mock_async_set_user_gps_from_location

        if gps_location:
            assert data['user']['lat'] == 12.02
            assert data['user']['lng'] == -15.04
            assert len(fn_inputs) == 0

        else:
            args, kwargs = fn_inputs[-1]
            assert kwargs == {'user_id': data['user']['id'], 'location': 'Elwood'}


@pytest.mark.parametrize("user_id_accessor, is_vendor, is_groupaccount, roles, tier, status_code", [
    (lambda o: o.id, False, False, [], 'subadmin', 403),
    (lambda o: o.id, True, False, ['vendor'], 'admin', 200),
    (lambda o: o.id, False, True, ['group_account'], 'admin', 200),
    (lambda o: 1222103, False, False, [], 'admin', 404),
])
def test_edit_user(test_client, authed_sempo_admin_user, create_transfer_account_user, user_id_accessor, is_vendor, is_groupaccount, roles, tier, status_code):
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
            'account_types': roles
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
    create_transfer_account_user.pin_hash = 'FAKE PIN HASH!'
    original_pin_hash = create_transfer_account_user.pin_hash
    original_otc = create_transfer_account_user.one_time_code

    response = test_client.post('/api/v1/user/reset_pin/',
                                headers=dict(Authorization=auth, Accept='application/json'),
                                data=json.dumps(dict(user_id=user_id)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
    if response.status_code == 200:
        assert original_pin_hash != create_transfer_account_user.pin_hash
        assert not create_transfer_account_user.pin_hash
        assert int(create_transfer_account_user.one_time_code) >= 0 <=9999
        assert create_transfer_account_user.one_time_code != original_otc

@pytest.mark.parametrize("user_id_accessor, tier, message, status_code", [
    (lambda o: o.id, 'admin', "user does not have any of the allowed roles", 403),
    (lambda o: o.id, 'superadmin', "pending", 400),
    (lambda o: o.id, 'superadmin', "Balance must be zero", 400),
    (lambda o: o.id, 'superadmin', "deleted", 200),
    (lambda o: o.id, 'superadmin', 'Resource Already Deleted', 400),
    (lambda o: 1222103, 'superadmin', 'No User Found for ID', 404),
])
def test_delete_user(test_client, authed_sempo_admin_user, create_transfer_account_user, create_credit_transfer,
                     user_id_accessor, tier, message, status_code):
    create_transfer_account_user.transfer_account.set_balance_offset(1000)

    if message == 'Balance must be zero' or message == 'Resource Already Deleted':
        create_credit_transfer.resolve_as_rejected()
        db.session.commit()

    if message == 'deleted':
        create_credit_transfer.resolve_as_complete()
        db.session.commit()

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
    assert message in response.json['message']  # in operator as annoying to make ID dynamic

    if create_credit_transfer.transfer_status == TransferStatusEnum.PENDING:
        create_credit_transfer.resolve_as_rejected()
        db.session.commit()


def test_get_user(test_client, authed_sempo_admin_user, create_transfer_account_user):
    # Checks that the get_user endpoint supports multiple organisations
    from server.models.organisation import Organisation
    master_organisation = Organisation.master_organisation()
    authed_sempo_admin_user.organisations.append(master_organisation)
    create_transfer_account_user.organisations = [master_organisation]
    db.session.commit()

    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)

    def get_user_endpoint(query_organisations):
        return test_client.get(
            f"/api/v1/user/?query_organisations={query_organisations}",
            headers=dict(
                Authorization=auth,
                Accept='application/json'
            ))

    def get_transfer_account_ids(users):
        transfer_account_ids = []
        for user in users:
            transfer_account_ids.append(user['id'])
        return transfer_account_ids

    # User 1 is in both orgs
    # User 3 is in Org 2
    # User 4 is in Org 2
    # User 5 is in Org 2
    # User 6 is in Org 2
    response = get_user_endpoint('1,2')
    assert response.status_code == 200
    users_list = response.json['data']['users']
    assert get_transfer_account_ids(users_list) == [6, 5, 4, 3, 1]

    response = get_user_endpoint('1')
    assert response.status_code == 200
    users_list = response.json['data']['users']
    assert get_transfer_account_ids(users_list) == [1]


    response = get_user_endpoint('2')
    assert response.status_code == 200
    users_list = response.json['data']['users']
    assert get_transfer_account_ids(users_list) == [6, 5, 4, 3, 1]

def test_create_user_via_kobo(test_client, init_database, authed_sempo_admin_user):

    org = Organisation.query.first()

    basic_auth = 'Basic ' + base64.b64encode(
        bytes(org.external_auth_username + ":" + org.external_auth_password, 'ascii')).decode('ascii')

    phone = '+61400000999'

    payload = {
        "_id": 119743701,
        "_notes": [],
        "First_Name": "Moo",
        "Last_Name": "Snoo",
        "Phone": phone,
        'my_attribute': 'yes_please',
        "Gender": "female",
        "_uuid": "43b023dd-ba68-4750-b499-3e7a85b8d1c3",
        "_bamboo_dataset_id": "",
        "_tags": [],
        "_xform_id_string": "a6kbSC3wnaRm62EwYN2vtM",
        "meta/instanceID": "uuid:43b023dd-ba68-4750-b499-3e7a85b8d1c3",
        "formhub/uuid": "9f92a0abbeca40d7923849ed78dbb73c",
        "end": "2020-09-01T21:30:45.153+10:00",
        "_submission_time": "2020-09-01T11:31:54",
        "_attachments": [],
        "start": "2020-09-01T21:30:29.825+10:00",
        "_geolocation": [
            "null",
            "null"
        ],
        "_validation_status": {},
        "_status": "submitted_via_web",
        "__version__": "vqAzPD373xq4zc7tqsYuVJ"
    }

    response = test_client.post(
        "/api/v1/user/?preprocess=true",
        headers=dict(
            Authorization=basic_auth,
            Accept='application/json'
        ),
        json=payload)

    data = response.json['data']

    assert data['user']['first_name'] == 'Moo'
    assert data['user']['last_name'] == 'Snoo'
    assert data['user']['phone'] == phone
    assert data['user']['custom_attributes']['gender'] == 'female'
    assert data['user']['custom_attributes']['my_attribute'] == 'yes_please'
    assert len(data['user']['custom_attributes']) == 2

def test_user_history(test_client, authed_sempo_admin_user, create_transfer_account_user_function):
    user = create_transfer_account_user(first_name='Transfer',
                                        last_name='User 3',
                                        phone=Faker().msisdn())
    db.session.commit()

    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)
    # Update a bunch of stuff
    test_client.put(
        f"/api/v1/transfer_account/{user.id}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'transfer_account_name': 'Sample Account',
            'approve': True,
            'notes': 'This account has a comment!'
    })

    response = test_client.put(
        f"/api/v1/user/{user.id}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        json={
            'first_name': 'Alf',
        })

    result = test_client.get(
        f"/api/v1/user/history/{user.id}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ))

    # Zero the dates because they'll change each time the tests are run
    result.json['data']['changes'][0]['created'] = None
    result.json['data']['changes'][0]['change_by'] = None
    assert result.json == {
        'data': {
            'changes': [
                {'change_by': None, 
                'column_name': 'first_name', 'created': None, 'new_value': 'Alf', 'old_value': 'Transfer'}
            ]
        },
        'message': 'Successfully Loaded.', 'status': 'success'
    }
