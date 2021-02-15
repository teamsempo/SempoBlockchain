import pytest
from server.utils.auth import get_complete_auth_token
from server.utils import executor
from server import red
import json

def test_dataset_api(test_client, authed_sempo_admin_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    fake_id = 'abc'
    response = test_client.get(
        f"/api/v1/async/{fake_id}/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
    )
    assert response.json == {'message': 'Async job with ID abc for user 1 does not exist!'}

    new_key = executor.get_job_key(1, 'abcd-efgh-ijkl')
    red.set(new_key, json.dumps({'data': 'alf'}))

    response = test_client.get(
        f"/api/v1/async/abcd-efgh-ijkl/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
    )
    assert response.json == {'data': 'alf'}
