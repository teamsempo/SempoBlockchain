import pytest
from server.utils import credit_transfer as CreditTransferUtils


def test_cents_to_dollars():
    assert CreditTransferUtils.cents_to_dollars(100) == 1


def tets_dollars_to_cents():
    assert CreditTransferUtils.dollars_to_cents(1) == 100

# @pytest.mark.parametrize("last_name, location, lat, lng, initial_disbursement", [
#     ('Hound', 'Melbourne, Victoria Australia', -37.8104277, 144.9629153, 400),
#     ('Hound', 'Melbourne, Victoria Australia', None, None, 400),
#     ('Hound', None, -37.8104277, 144.9629153, 400),
#     (None, None, None, None, None)
# ])
# def test_make_payment_transfer(test_client, init_database):
