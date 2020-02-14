"""
This file tests search_api.py.
"""
import json, pytest
from time import sleep
from server.utils.auth import get_complete_auth_token
from server.utils.user import create_transfer_account_user
from server import db

def test_transfer_usage_api_get(test_client, complete_admin_auth_token, create_organisation):
    """
    GIVEN a Flask application
    WHEN the '/api/transfer_usage/' page is requested (GET)
    THEN check the response has status 200 and a list
    """

    # This is a hack because the test DB isn't being built with migrations (and thus doesn't have tsvectors)
    db.session.execute("drop table search_view;")
    db.session.execute('''
        CREATE MATERIALIZED VIEW search_view AS (
            SELECT
                u.id,
                u.email,
                u._phone,
                u.first_name,
                u.last_name,
                u.default_transfer_account_id,
                to_tsvector(u.email) AS tsv_email,
                to_tsvector(u._phone) AS tsv_phone,
                to_tsvector(u.first_name) AS tsv_first_name,
                to_tsvector(u.last_name) AS tsv_last_name
            FROM "user" u
        );
    ''')

    # Adds users we're searching for
    create_transfer_account_user(first_name='Michiel',
                                    last_name='deRoos',
                                    phone="+19025551234",
                                    organisation=create_organisation)
    create_transfer_account_user(first_name='Francine',
                                    last_name='deRoos',
                                    phone="+19025552345",
                                    organisation=create_organisation)
    create_transfer_account_user(first_name='Roy',
                                    last_name='Donk',
                                    phone="+19025553456",
                                    organisation=create_organisation)
    db.session.commit()
    # Manually refresh tsvectors because the test DB has no triggers either
    db.session.execute("REFRESH MATERIALIZED VIEW search_view;")

    expected_results = {
        '': ['Roy', 'Francine', 'Michiel'], # Empty string should return everyone
        'fra': ['Francine'], # Only user starting with 'fra' substring is Francine
        'fra der': ['Francine', "Michiel"], # 'fra der' should return Francine first. Michiel 2nd, because it still matches _something_
        'mic der': ['Michiel', "Francine"] # 'fra der' should return Michiel first. Francine 2nd, because it still matches _something_
    }

    for e in expected_results:
        response = test_client.get('/api/v1/search/?search_string={}&search_type=transfer_accounts'.format(e),
                                headers=dict(
                                Authorization=complete_admin_auth_token, Accept='application/json'),
                                follow_redirects=True)
        transfer_accounts = response.json['data']['transfer_accounts']
        assert response.status_code == 200
        user_names = []
        for transfer_account in transfer_accounts:
            if transfer_account['users']:
                user_names.append(transfer_account['users'][0]['first_name'])
        assert expected_results[e] == user_names
    db.session.execute('DROP MATERIALIZED VIEW search_view CASCADE;')
    db.session.commit()
