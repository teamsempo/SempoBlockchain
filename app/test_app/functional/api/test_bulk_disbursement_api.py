"""
This file tests search_api.py.
"""
import json, pytest
from time import sleep
from server.models.user import User
from server.utils.auth import get_complete_auth_token
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server.utils.transfer_enums import TransferStatusEnum
from server import db
from server.utils.executor import get_job_result
from server.models.credit_transfer import CreditTransfer
from flask import current_app

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
    create_organisation.queried_org_level_transfer_account.set_balance_offset(10000000000)
    # Start the disbursement
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
    
    assert response.status_code == response_status
    if response_status == 201:
        assert response.status_code == 201

        assert response.json['data']['disbursement']['recipient_count'] == expected_recipient_count
        assert response.json['data']['disbursement']['total_disbursement_amount'] == expected_total_disbursement_amount

        resp_id = response.json['data']['disbursement']['id']

        # Check that the pending transactions are completed after APPROVE!
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=complete_admin_auth_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)

        transfers = CreditTransfer.query.all()

        for t in transfers:
            assert t.recipient_user.first_name in recipient_firstnames
            assert t.transfer_status == TransferStatusEnum.COMPLETE
            assert t.transfer_amount == disbursement_amount
        
        get_response = test_client.get(f'/api/v1/disbursement/{resp_id}',
                        headers=dict(
                        Authorization=complete_admin_auth_token, Accept='application/json'),
                        follow_redirects=True)
        accounts_from_response = get_response.json['data']['transfer_accounts']
        assert len(accounts_from_response) == expected_recipient_count
        for json_account in accounts_from_response:
            assert json_account['users'][0]['first_name'] in recipient_firstnames
            assert json_account['balance'] == disbursement_amount

        task_uuid = phase_two_response.json['task_uuid']
        async_result = json.loads(get_job_result(1, task_uuid))
        assert len(async_result['data']['credit_transfers']) == expected_recipient_count
        assert async_result['message'] == 'success'
        assert async_result['percent_complete'] == 100

        assert len(transfers) == expected_recipient_count
        
        for t in transfers:
            assert t.transfer_status == TransferStatusEnum.COMPLETE

        for t in transfers:
            db.session.delete(t)

@pytest.mark.parametrize("include_list, disbursement_amount, expected_recipient_count, expected_total_disbursement_amount\
     ,response_status, recipient_firstnames, multi_approval_setting, allowed_approvers_setting, statuses", [
    # No settings, approved right away
    ([5], 50, 1, 50, 201, ['Francine'], False, [], ['APPROVED', 'error', 'error', 'error', 'error']), 
    # Require multi-approval is on, only need two approvers
    ([5], 50, 1, 50, 201, ['Francine'], True, [], ['PARTIAL', 'APPROVED', 'error', 'error', 'error']), 
    # Require multi-approval with added allowed_approvers list. This can have n approvers, but is only approved once someone on the list approves
    ([5], 50, 1, 50, 201, ['Francine'], True, ['approver@withsempo.com'], ['PARTIAL', 'PARTIAL', 'PARTIAL', 'APPROVED', 'error']), 
])
def test_disbursement_approval_flow(include_list, disbursement_amount, expected_recipient_count, expected_total_disbursement_amount,\
    response_status, recipient_firstnames, multi_approval_setting, allowed_approvers_setting, statuses, test_client, complete_admin_auth_token\
    , create_organisation):
    """
    Tests the approval flow
    If there are no allowed_approvers in the config, but multi_approval_setting is True, it takes two users to approve
    If there are allowed_approvers in the config, and multi_approval_setting is True, it takes two users to approve and one must be in allowed_approvers
    If multi_approval_setting is False, it just takes one to approve
    """
    # Utility function to create admins to approve
    def make_new_user_and_token(name='francine', tier='superadmin'):
        user = User()
        user.create_admin_auth(email=name+'@withsempo.com', password='CalicoCat', tier=tier)
        user.organisations.append(create_organisation)
        user.default_organisation = create_organisation
        user.is_activated = True
        user.set_TFA_secret()
        user.TFA_enabled = True
        db.session.commit()
        return user, get_complete_auth_token(user)

    # Set the configs
    current_app.config['REQUIRE_MULTIPLE_APPROVALS'] = multi_approval_setting
    current_app.config['ALLOWED_APPROVERS'] = allowed_approvers_setting

    # Make the disbursement
    post_data = {
        "search_string": '',
        "params": '',
        "include_accounts": include_list,
        "exclude_accounts": [],
        "disbursement_amount": disbursement_amount
    }
    response = test_client.post(f'/api/v1/disbursement',
                            headers=dict(
                            Authorization=complete_admin_auth_token, Accept='application/json'),
                            json=post_data,
                            follow_redirects=True)
    
    assert response.status_code == response_status
    if response_status == 201:
        # Make superadmin 1, approve the first time
        approver_user, approver_token = make_new_user_and_token('test1', 'superadmin')
        resp_id = response.json['data']['disbursement']['id']
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=approver_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)
        if statuses[0] != 'error':
            assert phase_two_response.json['data']['disbursement']['state'] == statuses[0]
        else:
            assert phase_two_response.status_code not in [200, 201]

        # Make superadmin 2, approve the second time
        approver_user, approver_token = make_new_user_and_token('test2', 'superadmin')
        resp_id = response.json['data']['disbursement']['id']
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=approver_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)
        if statuses[1] != 'error':
            assert phase_two_response.json['data']['disbursement']['state'] == statuses[1]
        else:
            assert phase_two_response.status_code not in [200, 201]

        # Make superadmin 3, approve the third time
        approver_user, approver_token = make_new_user_and_token('test3', 'superadmin')
        resp_id = response.json['data']['disbursement']['id']
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=approver_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)
        if statuses[2] != 'error':
            assert phase_two_response.json['data']['disbursement']['state'] == statuses[2]
        else:
            assert phase_two_response.status_code not in [200, 201]

        # Make superadmin called approver, approve the third time
        approver_user, approver_token = make_new_user_and_token('approver', 'superadmin')
        resp_id = response.json['data']['disbursement']['id']
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=approver_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)
        if statuses[3] != 'error':
            assert phase_two_response.json['data']['disbursement']['state'] == statuses[3]
        else:
            assert phase_two_response.status_code not in [200, 201]

        # Clean up after self, verify the transfers
        transfers = CreditTransfer.query.all()
        assert len(transfers) == expected_recipient_count
        for t in transfers:
            assert t.recipient_user.first_name in recipient_firstnames
            assert t.transfer_status == TransferStatusEnum.COMPLETE
            assert t.transfer_amount == disbursement_amount
            db.session.delete(t)


@pytest.mark.parametrize("include_list, disbursement_amount, expected_recipient_count, expected_total_disbursement_amount\
     ,response_status, recipient_firstnames, multi_approval_setting, allowed_approvers_setting, statuses", [
    # No settings, approved right away
    ([5], 50, 1, 50, 201, ['Francine'], False, [], ['APPROVED', 'error']), 
    # Require multi-approval is on, sempodamin can still approve right away
    ([5], 50, 1, 50, 201, ['Francine'], True, [], ['APPROVED', 'error']), 
    # Require multi-approval is on, approvers list is in place, sempodamin can still approve right away
    ([5], 50, 1, 50, 201, ['Francine'], True, ['someuser'], ['APPROVED', 'error']), 
])
def test_sempoadmin_can_approve_anything(include_list, disbursement_amount, expected_recipient_count, expected_total_disbursement_amount,\
    response_status, recipient_firstnames, multi_approval_setting, allowed_approvers_setting, statuses, test_client, complete_admin_auth_token\
    , create_organisation):
    """
    Checks that sempoadmin can unilaterally approve a disbursement
    """
    # Utility function to create admins to approve
    def make_new_user_and_token(name='francine', tier='superadmin'):
        user = User()
        user.create_admin_auth(email=name+'@withsempo.com', password='CalicoCat', tier=tier)
        user.organisations.append(create_organisation)
        user.default_organisation = create_organisation
        user.is_activated = True
        user.set_TFA_secret()
        user.TFA_enabled = True
        db.session.commit()
        return user, get_complete_auth_token(user)

    # Set the configs
    current_app.config['REQUIRE_MULTIPLE_APPROVALS'] = multi_approval_setting
    current_app.config['ALLOWED_APPROVERS'] = allowed_approvers_setting

    # Make the disbursement
    post_data = {
        "search_string": '',
        "params": '',
        "include_accounts": include_list,
        "exclude_accounts": [],
        "disbursement_amount": disbursement_amount
    }
    response = test_client.post(f'/api/v1/disbursement',
                            headers=dict(
                            Authorization=complete_admin_auth_token, Accept='application/json'),
                            json=post_data,
                            follow_redirects=True)
    
    assert response.status_code == response_status
    if response_status == 201:
        # Make superadmin 1, approve the first time
        approver_user, approver_token = make_new_user_and_token('test1', 'sempoadmin')
        resp_id = response.json['data']['disbursement']['id']
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=approver_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)
        if statuses[0] != 'error':
            assert phase_two_response.json['data']['disbursement']['state'] == statuses[0]
        else:
            assert phase_two_response.status_code not in [200, 201]

        # Make superadmin 2, approve the second time
        approver_user, approver_token = make_new_user_and_token('test2', 'sempoadmin')
        resp_id = response.json['data']['disbursement']['id']
        phase_two_response = test_client.put(f'/api/v1/disbursement/{resp_id}',
            headers=dict(
            Authorization=approver_token, Accept='application/json'),
            json={ "action": "APPROVE" },
            follow_redirects=True)
        if statuses[1] != 'error':
            assert phase_two_response.json['data']['disbursement']['state'] == statuses[1]
        else:
            assert phase_two_response.status_code not in [200, 201]

        # Clean up after self, verify the transfers
        transfers = CreditTransfer.query.all()
        assert len(transfers) == expected_recipient_count
        for t in transfers:
            assert t.recipient_user.first_name in recipient_firstnames
            # Checking the individual transfer_status here, since the transfer status multi-approve logic
            # cascades from the disbursement action
            assert t.transfer_status == TransferStatusEnum.COMPLETE
            assert t.transfer_amount == disbursement_amount
            db.session.delete(t)
