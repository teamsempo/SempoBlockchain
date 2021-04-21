import pytest
from server.utils.auth import get_complete_auth_token
from server.models.attribute_map import AttributeMap

def test_attribute_map_api(test_client, complete_admin_auth_token, authed_sempo_admin_user):

    attribute = AttributeMap.query.filter_by(input_name='FooWoz').first()

    assert attribute is None

    response = test_client.post(
        '/api/v1/attribute_map/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'input_name': 'FooWoz',
            'output_name': 'MooBoop'
        })

    assert response.status_code == 200

    attribute = AttributeMap.query.filter_by(input_name='FooWoz').execution_options(show_all=True).first()

    assert attribute.input_name == 'FooWoz'
    assert attribute.output_name == 'MooBoop'
    assert attribute.organisation == authed_sempo_admin_user.default_organisation

    response = test_client.post(
        '/api/v1/attribute_map/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'input_name': 'FooWoz',
            'output_name': 'BarBah'
        })

    # Resubmitting should modify existing attribute
    atts = AttributeMap.query.filter_by(input_name='FooWoz').execution_options(show_all=True).all()
    assert response.status_code == 200
    assert len(atts) == 1
    assert atts[0].input_name == 'FooWoz'
    assert atts[0].output_name == 'BarBah'

    response = test_client.get(
        '/api/v1/attribute_map/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == 200
    assert response.json['data']['attribute_maps'] == [{'input_name': 'FooWoz', 'output_name': 'BarBah'}]

    response = test_client.get(
        f'/api/v1/attribute_map/{attribute.id}/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == 200
    assert response.json['data'] == {'input_name': 'FooWoz', 'output_name': 'BarBah'}

    response = test_client.delete(
        f'/api/v1/attribute_map/{attribute.id}/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == 200

    attribute = AttributeMap.query.filter_by(input_name='FooWoz').first()

    assert attribute is None