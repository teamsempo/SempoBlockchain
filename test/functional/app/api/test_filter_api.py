import pytest
from server.utils.auth import get_complete_auth_token


@pytest.mark.parametrize("tier, status_code", [
    ("subadmin", 401),
    ("admin", 200),
])
def test_get_filters(test_client, authed_sempo_admin_user, create_filter, tier, status_code):

    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.get(
        '/api/v1/filters/',
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ))
    assert response.status_code == status_code

    if status_code == 200:
        assert isinstance(response.json['data']['filters'], list)


@pytest.mark.parametrize("filter_name, filter_attributes, status_code", [
    (None, None, 400),
    ("TestFilter", None, 400),
    ("TestFilter 2", None,  400),
    ("TestFilter 2", dict(allowedValues=[1,2], id=1, keyName='balance', type='of'), 201),
])
def test_create_organisation(test_client, complete_admin_auth_token, create_filter,
                             filter_name, filter_attributes, status_code):

    response = test_client.post(
        '/api/v1/filters/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'filter_name': filter_name,
            'filter_attributes': filter_attributes
        })

    assert response.status_code == status_code

    if status_code == 201:
        assert response.json['data']['filter']['filter'] == create_filter.filter
        assert isinstance(response.json['data']['filter'], object)
