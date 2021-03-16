import pytest, json


@pytest.mark.parametrize("email, status_code", [("test@acme.org", 201)])
def test_me_export_api(test_client, create_transfer_account_user, email, status_code):
    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    response = test_client.post('/api/v1/me/export/',
                                headers=dict(Authorization=auth_token.decode(), Accept='application/json',
                                             ContentType='application/json'),
                                data=json.dumps(dict(date_range=None, amount=email)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code
    assert response.json['file_url'] is not None
