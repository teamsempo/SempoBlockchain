import pytest


@pytest.mark.parametrize("name, country_code, token_selector_func, status_code", [
    ("Test Org", 'AU', lambda t: t.id, 201),
    (None, None, lambda t: t.id, 400),
    ("Test Org", None, lambda t: t.id, 400),
    ("Test Org 2", 'asdf', lambda t: t.id, 400),
    ("New Test Org", 'AU', lambda t: 1932380198, 404),
])
def test_create_organisation(test_client, complete_admin_auth_token, external_reserve_token,
                             name, country_code, token_selector_func, status_code):

    response = test_client.post(
        '/api/v1/organisation/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'organisation_name': name,
            'token_id': token_selector_func(external_reserve_token),
            'country_code': country_code,
        })

    assert response.status_code == status_code

    if status_code == 201:
        assert response.json['data']['organisation']['primary_blockchain_address']


@pytest.mark.parametrize("org_selector_func, status_code", [
    (lambda o: o.id, 200),
    (lambda o: 1222103, 404),
])
def test_get_organisation(test_client, complete_admin_auth_token,
                          create_organisation, org_selector_func, status_code):
    response = test_client.get(
        f"/api/v1/organisation/{org_selector_func(create_organisation)}/",
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == status_code

