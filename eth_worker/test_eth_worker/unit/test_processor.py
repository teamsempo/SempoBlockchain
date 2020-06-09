import pytest

from utils import address
from test_eth_worker.helpers.mocks import MockUnbuiltTransaction


def test_get_gas_price(processor):
    assert processor.get_gas_price() == 100

# def test_call_contract_function(processor):
#     processor.call_contract_function()

# More of a functional test
def test_process_send_eth_transaction(processor, dummy_transaction, monkeypatch):

    ttt = processor.process_send_eth_transaction(
        dummy_transaction.id, address, 123

    )

#     test data in persisten to see if updated


@pytest.mark.parametrize("unbuilt_transaction, gas_limit, gas_price, should_error", [
    (MockUnbuiltTransaction(), None, 123456, False),
])
def test_compile_transaction_metadata(dummy_transaction, processor, unbuilt_transaction, gas_limit, gas_price, should_error):

    metadata = processor._compile_transaction_metadata(
        dummy_transaction.signing_wallet,
        dummy_transaction.id,
        unbuilt_transaction=unbuilt_transaction,
        gas_limit=gas_limit,
        gas_price=gas_price
    )

    tt = 4

# def test_process_send_eth_transaction(processor, dummy_transaction, monkeypatch):
#
#     processor.process_send_eth_transaction(
#         dummy_transaction.id, address, 123
#     )

# @pytest.fixture()
# def mock(mocker):
#     # Always patch out all sms sending apis because we don't want to spam messages with our tests!!
#     messages = []
#     def mock_sms_api(phone, message):
#         messages.append({'phone': phone, 'message': message})
#
#     mocker.patch('server.utils.phone._send_twilio_message.submit', mock_sms_api)
#     mocker.patch('server.utils.phone._send_messagebird_message.submit', mock_sms_api)
#     mocker.patch('server.utils.phone._send_at_message.submit', mock_sms_api)
#
#     return messages


# @pytest.mark.parametrize("tier, status_code", [
#     ("subadmin", 403),
#     ("admin", 200),
# ])
# def test_send_eth():
#
#     if tier:
#         authed_sempo_admin_user.set_held_role('ADMIN', tier)
#         auth = get_complete_auth_token(authed_sempo_admin_user)
#     else:
#         auth = None
#
#     response = test_client.get(
#         '/api/v1/filters/',
#         headers=dict(
#             Authorization=auth,
#             Accept='application/json'
#         ))
#     assert response.status_code == status_code
#
#     if status_code == 200:
#         assert isinstance(response.json['data']['filters'], list)
