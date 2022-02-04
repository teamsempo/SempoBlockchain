import server.utils.flutterwave as fw
from server.models.credit_transfer import CreditTransfer
from server.models.fiat_ramp import FiatRampDirection, FiatRampStatusEnum
from server.models.kyc_application import KycApplication
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum
from uuid import uuid4
import config
from server import db
import pytest


failed_state = {
    "status": "error",
    "code": "UNAUTHORIZED_ACCESS",
    "message": "Unauthorized access. Compliance approval required to use this feature"
}

success_state = {
    "status": "success",
    "message": "Transfer Queued Successfully",
}

# Basic test, make sure fiat ramp is created when it should be. Make sure it's resolved as completed right too!
@pytest.mark.parametrize("amount, expected_response, http_code, go_under_balance, succeed", [
    (1000, failed_state, 400, False, False),
    (5, failed_state, 400, True, False),
    (1000, success_state, 200, False, True),
])
def test_make_withdrawal(mocker, external_reserve_token, create_transfer_account_user, amount, expected_response, http_code, go_under_balance, succeed):
    # Make the user, KYC them up!
    create_transfer_account_user.default_organisation.country_code = 'UG'
    create_transfer_account_user.phone_number = '+19025551234'
    create_transfer_account_user.transfer_account._balance_offset_wei = 100000
    create_transfer_account_user.is_phone_verified = True
    external_reserve_token.float_account.is_phone_verified = True
    kyc = KycApplication(type='INDIVIDUAL')
    create_transfer_account_user.kyc_applications = [kyc]
    create_transfer_account_user.kyc_applications[0].kyc_status = 'VERIFIED'
    create_transfer_account_user.transfer_account.update_balance()
    external_reserve_token.symbol='UGX'

    ok_response_mock = mocker.MagicMock()
    type(ok_response_mock).status_code = mocker.PropertyMock(return_value=http_code)
    ok_response_mock.json.return_value = expected_response
    my_api_client_mock = mocker.MagicMock()
    my_api_client_mock.return_value = ok_response_mock
    
    mocker.patch('server.utils.flutterwave.requests.post', my_api_client_mock)


    credit_transfer = CreditTransfer(
        amount=amount,
        token=external_reserve_token,
        sender_user=create_transfer_account_user,
        recipient_transfer_account=external_reserve_token.float_account,
        transfer_type=TransferTypeEnum.WITHDRAWAL,
        transfer_subtype=TransferSubTypeEnum.STANDARD,
        uuid=str(uuid4()),
        require_sufficient_balance=False
    )
    assert credit_transfer.token.symbol == 'UGX'
    assert credit_transfer.fiat_ramp.payment_amount == credit_transfer.transfer_amount
    assert credit_transfer.fiat_ramp.payment_direction == FiatRampDirection.EGRESS
    assert credit_transfer.fiat_ramp.payment_status == FiatRampStatusEnum.PENDING
    credit_transfer.resolve_as_complete()

    if go_under_balance:
        assert credit_transfer.fiat_ramp.payment_metadata == {'message': 'Cannot complete payment as transfer does not meet transfer minimum value of 1000 UGX'}
        return True

    _, call = my_api_client_mock.call_args_list[0]
    
    assert call['url'] == 'https://api.flutterwave.com/v3/transfers'
    assert call['headers'] == {'Authorization': 'TEST_SECRET_KEY'}
    if not succeed:
        assert credit_transfer.fiat_ramp.payment_status == FiatRampStatusEnum.FAILED
        assert credit_transfer.fiat_ramp.payment_metadata == {'message': 'Unauthorized access. Compliance approval required to use this feature'}
    else:
        assert credit_transfer.fiat_ramp.payment_status == FiatRampStatusEnum.COMPLETE


# Makes sure we're not creating fiat ramps where we don't want them!
def test_fiat_ramp_off(external_reserve_token, create_transfer_account_user):
    external_reserve_token.symbol='UGX'
    credit_transfer = CreditTransfer(
        amount=1000,
        token=external_reserve_token,
        sender_user=create_transfer_account_user,
        recipient_user=create_transfer_account_user,
        transfer_type=TransferTypeEnum.PAYMENT,
        transfer_subtype=TransferSubTypeEnum.STANDARD,
        uuid=str(uuid4()),
        require_sufficient_balance=False
    )
    assert credit_transfer.token.symbol == 'UGX'
    assert credit_transfer.fiat_ramp == None
    credit_transfer.resolve_as_complete()
    assert credit_transfer.fiat_ramp == None

