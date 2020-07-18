import pytest
from server.exceptions import PaymentMethodException


def test_new_fiat_ramp(create_fiat_ramp):
    """
    GIVEN a FiatRamp model
    WHEN a new fiat ramp transfer is created
    THEN check transfer status is PENDING, then resolve as complete
    """
    from server.models.fiat_ramp import FiatRampStatusEnum

    assert isinstance(create_fiat_ramp.payment_amount, int)
    assert create_fiat_ramp.payment_amount == 100
    assert create_fiat_ramp.payment_reference is not None

    assert create_fiat_ramp.payment_status is FiatRampStatusEnum.PENDING

    create_fiat_ramp.resolve_as_complete_and_trigger_blockchain()

    assert create_fiat_ramp.payment_status is FiatRampStatusEnum.COMPLETE


def test_new_fiat_ramp_type_exception(create_fiat_ramp):
    """
    GIVEN a FiatRamp Model
    WHEN a new FiatRamp is created and the payment_method is not supported
    THEN check the PaymentMethodException is raised
    """
    with pytest.raises(PaymentMethodException):
        create_fiat_ramp.payment_method = 'UNSUPPORTED_PAYMENT_METHOD'
