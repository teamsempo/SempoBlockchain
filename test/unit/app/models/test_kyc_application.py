import pytest
from functools import partial

from helpers.kyc_application import KycApplicationFactory


@pytest.mark.parametrize("kyc_factory, expected", [
    (partial(KycApplicationFactory, type='BUSINESS'), (1, None)),
    (partial(KycApplicationFactory, type='INDIVIDUAL'), (1, 'PENDING')),
])
def test_create_kyc_application(kyc_factory, expected):
    kyc = kyc_factory()

    assert kyc.kyc_attempts == expected[0]
    assert kyc.kyc_status == expected[1]

