"""
This file tests search_api.py.
"""
import json, pytest
from time import sleep
from server.utils.auth import get_complete_auth_token
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server import db

def test_prep_search_api(test_client, complete_admin_auth_token, create_organisation):
    # This is a hack because the test DB isn't being built with migrations (and thus doesn't have trigrams)
    db.session.execute('''
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE INDEX trgm_first_name ON "user" USING gist (first_name gist_trgm_ops);
        CREATE INDEX trgm_last_name ON "user" USING gist (last_name gist_trgm_ops);
        CREATE INDEX trgm_phone ON "user" USING gist (_phone gist_trgm_ops);
        CREATE INDEX trgm_public_serial_number ON "user" USING gist (_public_serial_number gist_trgm_ops);
        CREATE INDEX trgm_primary_blockchain_address ON "user" USING gist (primary_blockchain_address gist_trgm_ops);
        CREATE INDEX trgm_location ON "user" USING gist (_location gist_trgm_ops);
    ''')

    # Adds users we're searching for
    create_transfer_account_user(first_name='Michiel',
                                    last_name='deRoos',
                                    phone='+19025551234',
                                    organisation=create_organisation,
                                    initial_disbursement = 100).location = 'Halifax'

    create_transfer_account_user(first_name='Francine',
                                    last_name='deRoos',
                                    phone='+19025552345',
                                    organisation=create_organisation,
                                    initial_disbursement = 200).location = 'Dartmouth'

    create_transfer_account_user(first_name='Roy',
                                    last_name='Donk',
                                    phone='+12345678901',
                                    organisation=create_organisation,
                                    initial_disbursement = 200).location = 'Burbank'

    create_transfer_account_user(first_name='Paul',
                                    last_name='Bufano',
                                    phone='+98765432123',
                                    organisation=create_organisation,
                                    initial_disbursement = 200).location = 'California'

    db.session.commit()

@pytest.mark.parametrize("search_term, results", [
    # Empty string should return everyone
    ('', ['Paul', 'Roy', 'Francine', 'Michiel']), 
    # First/Last Matching
    # Francine should be only result!
    ('fr', ['Francine']), 
    # Substrings match for all three, but this is clearly the right order!
    ('fra der', ['Francine', 'Michiel', 'Roy']), 
    # 'mic der' should return Michiel first. Francine 2nd, because it still matches _something_
    ('mic der', ['Michiel', "Francine", "Roy"]), 
    # Phone Matching
    # Roy is top dog here since this matches his phone number best, and phone number match is top priority
    ('12345678901 mic', ['Roy', 'Michiel', 'Francine', 'Paul']), 
    # 902 area code should float Michiel and Francine to the top
    # M added to query since the ranks were tied and I had to make one pull ahead for consistency!
    ('902 Mic f', ['Michiel', 'Francine', 'Paul']), 
    # Location matching
    # Michiel is from Halifax, so Michiel should be first here!
    ('Halifax', ['Michiel', 'Paul']), 
    # Michiel is from Halifax and Francine is from Dartmouth, so they should be at the top
    ('Dartmouth Halifax', ['Francine', 'Michiel', 'Paul', 'Roy']), 
])
def test_normal_search(search_term, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/search/' page is requested with search parameters
    check that the results are in the correct order
    """

    response = test_client.get(f'/api/v1/search/?search_string={search_term}',
                            headers=dict(
                            Authorization=complete_admin_auth_token, Accept='application/json'),
                            follow_redirects=True)

    transfer_accounts = response.json['data']['transfer_accounts']
    assert response.status_code == 200
    user_names = []
    for transfer_account in transfer_accounts:
        if transfer_account['users']:
            user_names.append(transfer_account['users'][0]['first_name'])
    assert results == user_names

@pytest.mark.parametrize("search_term, filters, results", [
    # Location filter with query string
    ('902', "_location(IN)(Halifax)", ['Michiel']),
    ('902', "_location(IN)(Dartmouth)", ['Francine']),
    ('902', "_location(IN)(Halifax,Dartmouth)", ['Michiel', 'Francine']),
    # Location filter without query string
    ('', "_location(IN)(Halifax)", ['Michiel']),
    ('', "_location(IN)(Dartmouth)", ['Francine']),
    ('', "_location(IN)(Halifax,Dartmouth)", ['Michiel', 'Francine']),
])
def test_filtered_search(search_term, filters, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/search/' page is requested with filters
    check that the results are in the correct order
    """
    response = test_client.get(f'/api/v1/search/?search_string={search_term}&search_type=transfer_accounts&params={filters}',
                        headers=dict(
                        Authorization=complete_admin_auth_token, Accept='application/json'),
                        follow_redirects=True)
    transfer_accounts = response.json['data']['transfer_accounts']
    assert response.status_code == 200
    user_names = []
    for transfer_account in transfer_accounts:
        if transfer_account['users']:
            user_names.append(transfer_account['users'][0]['first_name'])
    assert results.sort() == user_names.sort()

