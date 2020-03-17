"""
This file tests search_api.py.
"""
import json, pytest
from time import sleep
from server.utils.auth import get_complete_auth_token
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server import db

def test_search_api(test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/search/' page is requested with search parameters
    check that the results are in the correct order
    """

    # This is a hack because the test DB isn't being built with migrations (and thus doesn't have tsvectors)
    db.session.execute("drop table search_view;")
    db.session.commit()
    db.session.execute('''
        CREATE MATERIALIZED VIEW search_view AS (
            SELECT
                u.id,
                u.email,
                u._phone,
                u.first_name,
                u.last_name,
                u._public_serial_number,
                u._location,
                u.primary_blockchain_address,
                u.default_transfer_account_id,
                to_tsvector(u.email) AS tsv_email,
                to_tsvector(u._phone) AS tsv_phone,
                to_tsvector(u.first_name) AS tsv_first_name,
                to_tsvector(u.last_name) AS tsv_last_name,
                to_tsvector(u._public_serial_number) AS tsv_public_serial_number,
                to_tsvector(u._location) AS tsv_location,
                to_tsvector(u.primary_blockchain_address) AS tsv_primary_blockchain_address,
                to_tsvector(CAST (u.default_transfer_account_id AS VARCHAR(10))) AS tsv_default_transfer_account_id
            FROM "user" u
        );
    ''')

    male_attribute = {
        "custom_attributes": {
            "gender": "male"
        }
    }

    female_attribute = {
        "custom_attributes": {
            "gender": "male"
        }
    }

    # Adds users we're searching for
    michiel = create_transfer_account_user(first_name='Michiel',
                                    last_name='deRoos',
                                    phone="+19025551234",
                                    organisation=create_organisation,
                                    initial_disbursement = 100)


    francine = create_transfer_account_user(first_name='Francine',
                                    last_name='deRoos',
                                    phone="+19025552345",
                                    organisation=create_organisation,
                                    initial_disbursement = 200)

    roy = create_transfer_account_user(first_name='Roy',
                                    last_name='Donk',
                                    phone="+19025553456",
                                    organisation=create_organisation,
                                    initial_disbursement = 200)

    db.session.commit()
    # Manually refresh tsvectors because the test DB has no triggers either
    db.session.execute("REFRESH MATERIALIZED VIEW search_view;")

    # --Tests for standard search--
    expected_results = {
        '': ['Roy', 'Francine', 'Michiel'], # Empty string should return everyone
        'fra': ['Francine'], # Only user starting with 'fra' substring is Francine
        'fra der': ['Francine', "Michiel"], # 'fra der' should return Francine first. Michiel 2nd, because it still matches _something_
        'mic der': ['Michiel', "Francine"] # 'fra der' should return Michiel first. Francine 2nd, because it still matches _something_
    }
    for search_term in expected_results:
        response = test_client.get('/api/v1/search/?search_string={}&search_type=transfer_accounts'.format(search_term),
                                headers=dict(
                                Authorization=complete_admin_auth_token, Accept='application/json'),
                                follow_redirects=True)
        transfer_accounts = response.json['data']['transfer_accounts']
        assert response.status_code == 200
        user_names = []
        for transfer_account in transfer_accounts:
            if transfer_account['users']:
                user_names.append(transfer_account['users'][0]['first_name'])
        assert expected_results[search_term] == user_names

    # --Tests for filters and sorting--

    expected_results = {
        ('', '%$user_filters%,rounded_account_balance%<20%'): ['Roy', 'Francine', 'Michiel'],
        ('', '%$user_filters%,rounded_account_balance%>100%'): [],
    }
    for (search_term, filters), expected_result in expected_results.items():
        response = test_client.get('/api/v1/search/?search_string={}&search_type=transfer_accounts&params={}'.format(search_term, filters),
                            headers=dict(
                            Authorization=complete_admin_auth_token, Accept='application/json'),
                            follow_redirects=True)
        transfer_accounts = response.json['data']['transfer_accounts']
        assert response.status_code == 200
        user_names = []
        for transfer_account in transfer_accounts:
            if transfer_account['users']:
                user_names.append(transfer_account['users'][0]['first_name'])
        assert expected_result == user_names
    db.session.execute('DROP MATERIALIZED VIEW search_view CASCADE;')
    db.session.commit()

