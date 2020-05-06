from server.utils import credit_transfer as CreditTransferUtils


def test_cents_to_dollars():
    assert CreditTransferUtils.cents_to_dollars(100) == 1


def tets_dollars_to_cents():
    assert CreditTransferUtils.dollars_to_cents(1) == 100
