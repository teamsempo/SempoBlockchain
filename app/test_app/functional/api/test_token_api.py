import pytest, json
from server.utils.auth import get_complete_auth_token


def test_get_token(test_client, authed_sempo_admin_user, create_transfer_account_user):
    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)

    token_response = test_client.get(
        f"/api/v1/token/",
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ))

    assert token_response.status_code == 200
    assert len(token_response.json['data']['tokens']) <= 1


@pytest.mark.parametrize("name,symbol,address,decimals,chain,tier,status_code", [
    (None, None, None, None, None, 'admin', 403),  # unauthorised
    ('USD Coin', 'USDC', None, 18, 'ETHEREUM', 'superadmin', 400),  # no address
    ('USD Coin', 'USDC', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 18, 'ETHEREUM', 'superadmin', 201),  # created
    ('USD Coin', 'USDC', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 18, 'ETHEREUM', 'superadmin', 400),  # dupe token
])
def test_create_token(
        test_client, authed_sempo_admin_user, name, symbol, decimals, address, chain, tier, status_code
):
    authed_sempo_admin_user.set_held_role('ADMIN', tier)
    auth = get_complete_auth_token(authed_sempo_admin_user)

    response = test_client.post('/api/v1/token/',
                                headers=dict(Authorization=auth, Accept='application/json'),
                                data=json.dumps(
                                    dict(name=name, symbol=symbol, decimals=decimals, address=address, chain=chain)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
