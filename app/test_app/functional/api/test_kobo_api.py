import base64

from faker.providers import phone_number
from faker import Faker

from server.models.organisation import Organisation

fake = Faker()
fake.add_provider(phone_number)

def test_create_user_via_kobo(test_client, init_database, authed_sempo_admin_user):

    org = Organisation.query.first()

    basic_auth = 'Basic ' + base64.b64encode(
        bytes(org.external_auth_username + ":" + org.external_auth_password, 'ascii')).decode('ascii')

    phone = '+' + fake.msisdn()

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
        "/api/v1/kobo/user/",
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