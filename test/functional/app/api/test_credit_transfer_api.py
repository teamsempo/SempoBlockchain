import pytest

# todo- get credit transfers / post credit transfers / put credit transfer


@pytest.mark.parametrize("credit_transfer_selector_func, status_code", [
    (lambda o: o.id, 200),
    (lambda o: 1222103, 404),
])
def test_get_single_credit_transfer(test_client, complete_admin_auth_token, create_credit_transfer,
                          credit_transfer_selector_func, status_code):
    response = test_client.get(
        f"/api/v1/credit_transfer/{credit_transfer_selector_func(create_credit_transfer) or ""}",
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ))

    assert response.status_code == status_code

