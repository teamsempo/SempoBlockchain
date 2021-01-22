"""
This file tests search_api.py.
"""
import json, pytest
from time import sleep
from server.utils.auth import get_complete_auth_token
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server.utils.transfer_enums import TransferStatusEnum
from server import db
from server.models.credit_transfer import CreditTransfer

def test_prep_bulk_disbursement_api(test_client, complete_admin_auth_token, create_organisation):
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


@pytest.mark.parametrize("search_string, params, include_list, exclude_list, disbursement_amount, expected_recipient_count,\
     expected_total_disbursement_amount, response_status, recipient_firstnames", [
    # Empty string should disburse to everyone
    ('', '', [], [], 50, 4, 200, 201, ['Paul', 'Roy', 'Francine', 'Michiel']), 
    ('', '_location(IN)(Halifax)', [], [], 50, 1, 50, 201, ['Michiel']), 
    ('', '', [], [5], 50, 3, 150, 201, ['Paul', 'Roy', 'Michiel']), 
    ('', '', [5], [], 50, 1, 50, 201, ['Francine']), 
])
def test_disbursement(search_string, params, include_list, exclude_list, disbursement_amount, expected_recipient_count,\
    expected_total_disbursement_amount, test_client, complete_admin_auth_token, create_organisation, response_status, recipient_firstnames):
    """
    When the '/api/v1/disbursement/' is POSTed to with search parameters
    check that the right disbursements are set up!
    Also checks GET '/api/v1/disbursement/{id}' for that disbursement, and activating it with POST!
    """

    post_data = {
        "search_string": search_string,
        "params": params,
        "include_accounts": include_list,
        "exclude_accounts": exclude_list,
        "disbursement_amount": disbursement_amount
    }
    response = test_client.post(f'/api/v1/disbursement',
                            headers=dict(
                            Authorization=complete_admin_auth_token, Accept='application/json'),
                            json=post_data,
                            follow_redirects=True)

    response.status_code == response_status
    if response_status == 201:
        transfers = CreditTransfer.query.all()
        assert response.status_code == 201
        assert response.json['recipient_count'] == expected_recipient_count
        assert response.json['total_disbursement_amount'] == expected_total_disbursement_amount
        assert len(transfers) == expected_recipient_count

        # Check that everything is correct with the generated PENDING transactions
        resp_id = response.json['disbursement_id']
        for t in transfers:
            assert t.recipient_user.first_name in recipient_firstnames
            assert t.transfer_status == TransferStatusEnum.PENDING
            assert t.transfer_amount == disbursement_amount
        
            get_response = test_client.get(f'/api/v1/disbursement/{resp_id}',
                            headers=dict(
                            Authorization=complete_admin_auth_token, Accept='application/json'),
                            follow_redirects=True)
            transfers_from_response = get_response.json['data']['credit_transfers']
            assert len(transfers_from_response) == expected_recipient_count
            for json_transfer in transfers_from_response:
                assert json_transfer['recipient_user']['first_name' ] in recipient_firstnames
                assert json_transfer['transfer_amount'] == disbursement_amount

        # Check that the pending transactions are completed after EXECUTE!
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=complete_admin_auth_token, Accept='application/json'),
            json={ "action": "EXECUTE" },
            follow_redirects=True)

        assert phase_two_response.json == {'status': 'success'}
        transfers = CreditTransfer.query.all()
        for t in transfers:
            assert t.transfer_status == TransferStatusEnum.COMPLETE

        # Remove old transfers for the next test!
        for t in transfers:
            db.session.delete(t)
