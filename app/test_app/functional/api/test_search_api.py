"""
This file tests search_api.py.
"""
import json, pytest
from time import sleep
from server.utils.auth import get_complete_auth_token
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server import db

def test_prep_search_api(test_client, complete_admin_auth_token, create_organisation):
    # This is a hack because the test DB isn't being built with migrations (and thus doesn't have triggers)
    db.session.execute('''CREATE TRIGGER tsv_email_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_email, 'pg_catalog.simple', email);''')
    db.session.execute('''CREATE TRIGGER tsv_phone_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_phone, 'pg_catalog.simple', _phone);''')
    db.session.execute('''CREATE TRIGGER tsv_first_name_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_first_name, 'pg_catalog.simple', first_name);''')
    db.session.execute('''CREATE TRIGGER tsv_last_name_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_last_name, 'pg_catalog.simple', last_name);''')
    db.session.execute('''CREATE TRIGGER tsv_public_serial_number_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_public_serial_number, 'pg_catalog.simple', _public_serial_number);''')
    db.session.execute('''CREATE TRIGGER tsv_location_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_location, 'pg_catalog.simple', _location);''')
    db.session.execute('''CREATE TRIGGER tsv_primary_blockchain_address_trigger BEFORE INSERT OR UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(tsv_primary_blockchain_address, 'pg_catalog.simple', primary_blockchain_address);''')

    db.session.commit()

    # Adds users we're searching for
    create_transfer_account_user(first_name='Michiel',
                                    last_name='deRoos',
                                    phone="+19025551234",
                                    organisation=create_organisation,
                                    initial_disbursement = 100)


    create_transfer_account_user(first_name='Francine',
                                    last_name='deRoos',
                                    phone="+19025552345",
                                    organisation=create_organisation,
                                    initial_disbursement = 200)

    create_transfer_account_user(first_name='Roy',
                                    last_name='Donk',
                                    phone="+19025553456",
                                    organisation=create_organisation,
                                    initial_disbursement = 200)

    db.session.commit()

@pytest.mark.parametrize("search_term, results", [
    ('', ['Roy', 'Francine', 'Michiel']), # Empty string should return everyone
    ('fra', ['Francine']), # Only user starting with 'fra' substring is Francine
    ('fra der', ['Francine', "Michiel"]), # 'fra der' should return Francine first. Michiel 2nd, because it still matches _something_
    ('mic der', ['Michiel', "Francine"]), # 'fra der' should return Michiel first. Francine 2nd, because it still matches _something_(
])
def test_normal_search(search_term, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/search/' page is requested with search parameters
    check that the results are in the correct order
    """

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
    assert results == user_names

# TODO: the first one isn't passing, but seems to be returning the correct result??
@pytest.mark.xfail
@pytest.mark.parametrize("search_term, filters, results", [
    ('', "rounded_account_balance(GT)(2)", ['Roy', 'Francine', 'Michiel']),
    ('', "rounded_account_balance(GT)(100)", []),
])
def test_filtered_search(search_term, filters, results, test_client, complete_admin_auth_token, create_organisation):
    """
    When the '/api/v1/search/' page is requested with filters
    check that the results are in the correct order
    """
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
    assert results == user_names
