import pytest, json


@pytest.mark.parametrize("reset_user_id,status_code", [
    ("100", 404),
    (None, 400),
    ("1", 200),
])
def test_admin_reset_user_pin(test_client, complete_admin_auth_token, reset_user_id, status_code):
    response = test_client.post('/api/v1/user/reset_pin/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(user_id=reset_user_id)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
