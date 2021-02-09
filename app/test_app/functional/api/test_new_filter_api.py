import pytest
from server.utils.auth import get_complete_auth_token
import re 

def make_filter(filter_name, filter, auth_token, client):
    return client.post(
            '/api/v1/filter/',
            headers=dict(
                Authorization=auth_token,
                Accept='application/json'
            ),
            json={
                'filter_name': filter_name,
                'filter': filter
            })

def test_get_filters(test_client, complete_admin_auth_token):
    def get_filters():
        return test_client.get(
            '/api/v1/filter/',
            headers=dict(
                Authorization=complete_admin_auth_token,
                Accept='application/json'
            ))
    empty_filters = get_filters()
    assert empty_filters.json['message'] == 'success'
    assert empty_filters.json['data']['filters'] == []
    make_filter('Test Filter One', "rounded_transfer_amount(EQ)(1)", complete_admin_auth_token, test_client)
    one_filter = get_filters()
    assert one_filter.json['message'] == 'success'
    assert one_filter.json['data']['filters'][0]['filter'] == 'rounded_transfer_amount(EQ)(1)'
    assert one_filter.json['data']['filters'][0]['name'] == 'Test Filter One'


@pytest.mark.parametrize("filter_name, filter, message, status_code", [
    # Check parameters work
    (None, None, 'Must provide a filter object and name', 400),
    ("filter", None, 'Must provide a filter object and name', 400),
    (None, "rounded_transfer_amount(EQ)(1)", 'Must provide a filter object and name' , 400),
    # Check normal flow
    ("MyTestFilter", "rounded_transfer_amount(EQ)(1)", 'success', 201),
    # Check duplicate filter name
    ("MyTestFilter", "rounded_transfer_amount(EQ)(1)", 'Filter Name "MyTestFilter" already used.', 400),
    # Check invalid filter
    ("newTest", 'fake_table_bad_filter(EQ)(1)', 'Filter "fake_table_bad_filter(EQ)(1)" is invalid. Please provide a working filter!', 400),
])
def test_create_filters(test_client, complete_admin_auth_token, create_filter,
                             filter_name, filter, message, status_code):
    response = make_filter(filter_name, filter, complete_admin_auth_token, test_client)
    assert response.json['message'] == message
    assert response.status_code == status_code
    if status_code == 201:
        assert response.json['data']['filter']['name'] == filter_name
        assert response.json['data']['filter']['filter'] == filter

def test_delete_filter(test_client, complete_admin_auth_token, create_filter):
    # Check that you can delete
    response = make_filter('Michiel\'s Great Test Filter!', 'rounded_transfer_amount(EQ)(1)', complete_admin_auth_token, test_client)
    id = response.json['data']['filter']['id']
    delete_resp = test_client.delete(
        f'/api/v1/filter/{id}/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))
    assert delete_resp.json == {'message': 'success'}

    # Check that deleted item is really deleted
    # And that you can't delete something that doesn't exist!
    delete_resp = test_client.delete(
        f'/api/v1/filter/{id}/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))
    assert delete_resp.json == {'message': f'Filter "{id}" does not exist!'}

def test_get_filter(test_client, complete_admin_auth_token, create_filter):
    # Check that you can delete
    response = make_filter('Michiel\'s Great Test Filter!', 'rounded_transfer_amount(EQ)(1)', complete_admin_auth_token, test_client)
    id = response.json['data']['filter']['id']
    get_resp = test_client.get(
        f'/api/v1/filter/{id}/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))
        
    get_resp.json['data']['filter']['created'] = 'This doesn\'t matter'
    get_resp.json['data']['filter']['updated'] = 'This doesn\'t matter'

    assert get_resp.json == {'data': 
        {
            'filter': {
                'created': 'This doesn\'t matter', 
                'filter': 'rounded_transfer_amount(EQ)(1)', 
                'id': id, 
                'name': "Michiel's Great Test Filter!", 
                'updated': 'This doesn\'t matter'
            }
        }, 
        'message': 'success'
    }
