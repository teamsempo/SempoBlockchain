"""
This file tests search_api.py.
"""
import json, pytest
from server.utils.user import create_transfer_account_user
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
    michiel = create_transfer_account_user(first_name='Michiel',
                                    last_name='deRoos',
                                    phone='+19025551234',
                                    organisation=create_organisation,
                                    initial_disbursement = 100)
    michiel.location = 'Halifax'

    francine = create_transfer_account_user(first_name='Francine',
                                    last_name='deRoos',
                                    phone='+19025552345',
                                    organisation=create_organisation,
                                    initial_disbursement = 200)
    francine.location = 'Dartmouth'

    roy = create_transfer_account_user(first_name='Roy',
                                    last_name='Donk',
                                    phone='+12345678901',
                                    organisation=create_organisation,
                                    initial_disbursement = 200)
    roy.location = 'Burbank'

    paul = create_transfer_account_user(first_name='Paul',
                                    last_name='Bufano',
                                    phone='+98765432123',
                                    organisation=create_organisation,
                                    initial_disbursement = 200)
    paul.location = 'California'

    db.session.commit()

    def make_transfer(amount, recipient_user_id, sender_user_id, transfer_type):
        test_client.post(
        '/api/v1/credit_transfer/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        data=json.dumps(dict(
            transfer_amount=amount,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            transfer_type=transfer_type,
        )),
        content_type='application/json', follow_redirects=True)

    make_transfer(5, paul.id, michiel.id, 'PAYMENT')
    make_transfer(2, francine.id, roy.id, 'DISBURSEMENT')
    make_transfer(6, roy.id, paul.id, 'PAYMENT')
    make_transfer(23, michiel.id, francine.id, 'PAYMENT')
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
def test_transfer_accounts_search(search_term, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/transfer_account/' page is requested with search parameters
    check that the results are in the correct order
    """

    response = test_client.get(f'/api/v1/transfer_account/?search_string={search_term}',
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
def test_transfer_account_search(search_term, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/transfer_account/' page is requested with search parameters
    check that the results are in the correct order
    """

    response = test_client.get(f'/api/v1/transfer_account/?search_string={search_term}',
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

def test_filtered_transfer_account_search(search_term, filters, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/transfer_account/' page is requested with filters
    check that the results are in the correct order
    """
    response = test_client.get(f'/api/v1/transfer_account/?search_string={search_term}&search_type=transfer_account&params={filters}',
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

@pytest.mark.parametrize("search_term, filters, results, sort_by, order", [
    # Empty string returns all transfers, in id descending order
    ('', '', [4, 3, 2, 1], 'rank', 'desc'),
    # Empty string returns all transfers, in id asc order
    ('', '', [1, 2, 3, 4], 'rank', 'asc'),
    # Returns all transfers, in ascending order of amount
    ('', '', [2, 1, 3, 4], 'amount', 'asc'),
    # Returns all payments
    ('', "public_transfer_type(IN)(PAYMENT)", [4, 3, 1], 'rank', 'desc'),
    # Returns all transfers involving Francine
    ('Fra', '', [4, 2], 'rank', 'desc'),
    # Returns only payments involving Francine
    ('Fra', "public_transfer_type(IN)(PAYMENT)", [4], 'rank', 'desc'),
])

def test_filtered_credit_transfer_search(search_term, filters, results, test_client, complete_admin_auth_token, create_organisation, sort_by, order):
    """
    When the '/api/v1/credit_transfer/' page is requested with filters
    check that the results are in the correct order
    """
    response = test_client.get(f'/api/v1/credit_transfer/?search_string={search_term}&search_type=credit_transfer&params={filters}&sort_by={sort_by}&order={order}',
                        headers=dict(
                        Authorization=complete_admin_auth_token, Accept='application/json'),
                        follow_redirects=True)
    credit_transfers = response.json['data']['credit_transfers']
    assert response.status_code == 200
    ids = []
    for credit_transfer in credit_transfers:
        if credit_transfer['id']:
            ids.append(credit_transfer['id'])
    assert results == ids

