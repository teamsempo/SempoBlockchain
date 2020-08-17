"""
This file tests blockchain_taskable_api.py.
"""
import pytest
import config
import base64

from requests.auth import HTTPBasicAuth
from server.utils.transfer_enums import BlockchainStatus

def test_blockchain_taskable(create_credit_transfer, test_client):
    """
    GIVEN a CreditTransfer model
    WHEN an callback is received
    THEN the callback is saved to the CreditTransfer and WorkerMessages tables
    """
    fake_blockchain_uuid = '1234-5678-1234-5678'
    fake_hash = 'fran-cine-thec-at123'
    unix_time = 1587680203
    transfer = create_credit_transfer
    transfer.blockchain_task_uuid = fake_blockchain_uuid

    # Default status of pending
    assert transfer.blockchain_status == BlockchainStatus.PENDING

    # POST a PENDING status, but with a message!
    post_data = {
            'blockchain_task_uuid': fake_blockchain_uuid,
            'timestamp': unix_time,
            'blockchain_status': 'PENDING',
            'error': None,
            'message': 'Still Working!',
            'hash': fake_hash
        }
    callback_url = '/api/v1/blockchain_taskable'
    basic_auth = 'Basic ' + base64.b64encode(bytes(config.INTERNAL_AUTH_USERNAME + ":" + config.INTERNAL_AUTH_PASSWORD, 'ascii')).decode('ascii')

    test_client.post(callback_url,
        json=post_data,
        headers=dict(Authorization=basic_auth, Accept='application/json'),
    )
    # Check that the message is received
    assert transfer.blockchain_status == 'PENDING'
    assert transfer.messages[0].message == 'Still Working!'

    # Pushing the status back in time from a previous status will not change the status
    # I.e. this status shouldn't be pushed since the previously-received PENDING is 
    # the rightful status
    post_data['timestamp'] = post_data['timestamp']-6000
    post_data['blockchain_status'] = 'FAILED'
    test_client.post(callback_url,
        json=post_data,
        headers=dict(Authorization=basic_auth, Accept='application/json'),
    )
    assert transfer.blockchain_status == 'PENDING'

    # Conversely, hanging the status in the future will update the status 
    post_data['timestamp'] = post_data['timestamp']+12000
    post_data['blockchain_status'] = 'SUCCESS'
    test_client.post(callback_url,
        json=post_data,
        headers=dict(Authorization=basic_auth, Accept='application/json'),
    )
    assert transfer.blockchain_status == 'SUCCESS'

