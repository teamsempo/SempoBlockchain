import pytest, json, base64, config
from server.models.incentive import Incentive
from server.models.credit_transfer import CreditTransfer
from server import db
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum


def test_get_me_credit_transfer_api(test_client, create_credit_transfer, create_transfer_account_user):
    """
    GIVEN a Flask application
    WHEN '/api/me/credit_transfer/' is requested (GET)
    THEN check a list of credit transfers is returned
    """
    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    response = test_client.get('/api/v1/me/credit_transfer/',
                               headers=dict(Authorization=auth_token.decode(), Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 201
    assert response.json['data']['credit_transfers'][0]['id'] is create_credit_transfer.id

def test_valid_create_me_credit_transfer_api(
        test_client,
        create_transfer_account_user,
        create_transfer_account_user_2
):
    """
    Tests that a user can only send a transfer from an account they own
    """

    auth_token = create_transfer_account_user.encode_auth_token()

    ta1 = create_transfer_account_user.default_transfer_account
    ta2 = create_transfer_account_user_2.default_transfer_account

    ta1.is_approved = True
    ta2.is_approved = True

    ta1.set_balance_offset(1000)
    ta2.set_balance_offset(1000)


    response = test_client.post(
        '/api/v1/me/credit_transfer/',
        headers=dict(
            Authorization=auth_token.decode(),
            Accept='application/json'
        ),
        data=json.dumps(dict(
            is_sending=True,
            transfer_amount=10,
            my_transfer_account_id=ta1.id,
            transfer_account_id=ta2.id
        )),
        content_type='application/json', follow_redirects=True)

    assert response.status_code == 201

def test_invalid_create_me_credit_transfer_api(
        test_client,
        create_transfer_account_user,
        create_transfer_account_user_2
):
    """
    Tests that a user can only send a transfer from an account they own
    """

    auth_token = create_transfer_account_user.encode_auth_token()

    ta1 = create_transfer_account_user.default_transfer_account
    ta2 = create_transfer_account_user_2.default_transfer_account

    ta1.is_approved = True
    ta2.is_approved = True

    ta1.set_balance_offset(1000)
    ta2.set_balance_offset(1000)


    response = test_client.post(
        '/api/v1/me/credit_transfer/',
        headers=dict(
            Authorization=auth_token.decode(),
            Accept='application/json'
        ),
        data=json.dumps(dict(
            is_sending=True,
            transfer_amount=10,
            my_transfer_account_id=ta2.id,
            transfer_account_id=ta1.id
        )),
        content_type='application/json', follow_redirects=True)

    assert response.status_code == 401

@pytest.mark.parametrize('incentive, status, amount', [
    # Gives 50% incentive
    (Incentive(incentive_rules = {
        'transfer_method': 'ANY',
        'incentive_type': 'PERCENTAGE',
        'incentive_amount': 50,
        'incentive_recipient': 'RECIPIENT',
        'restrictions': [
            {
                'style': 'transaction_count',
                'days': 7,
                'transactions': 5
            },
            {
                'style': 'currency',
                'days': 7,
                'limit': 5000
            }
        ],
    }), 
    201,
    5.0),
    # Gives 200 units fixed incentive
    (Incentive(incentive_rules = {
        'transfer_method': 'ANY',
        'incentive_type': 'FIXED',
        'incentive_amount': 200,
        'incentive_recipient': 'RECIPIENT',
        'restrictions': [
            {
                'style': 'transaction_count',
                'days': 7,
                'transactions': 5
            },
            {
                'style': 'currency',
                'days': 7,
                'limit': 5000
            }
        ],
    }), 
    201,
    200),
    # Fail by transaction count
    (Incentive(incentive_rules = {
        'transfer_method': 'ANY',
        'incentive_type': 'FIXED',
        'incentive_amount': 100,
        'incentive_recipient': 'RECIPIENT',
        'restrictions': [
            {
                'style': 'transaction_count',
                'days': 1,
                'transactions': 0
            },
            {
                'style': 'currency',
                'days': 7,
                'limit': 5000
            }
        ],
    }), 
    400,
    None),
    # Fail by currency
    (Incentive(incentive_rules = {
        'transfer_method': 'ANY',
        'incentive_type': 'PERCENTAGE',
        'incentive_amount': 100,
        'incentive_recipient': 'RECIPIENT',
        'restrictions': [
            {
                'style': 'transaction_count',
                'days': 7,
                'transactions': 5
            },
            {
                'style': 'currency',
                'days': 7,
                'limit': 0
            }
        ],
    }), 
    400,
    None),
])
def test_create_me_credit_transfer_api_with_incentive(
        test_client,
        create_transfer_account_user,
        create_transfer_account_user_2,
        incentive,
        status,
        amount
):
    """
    Tests that a incentives are executed on credit transfers
    """
    Incentive.query.delete()
    incentive.organisation=create_transfer_account_user.default_organisation

    create_transfer_account_user.default_organisation.org_level_transfer_account.set_balance_offset(100000)
    create_transfer_account_user.default_organisation.org_level_transfer_account.is_approved = True
    db.session.add(incentive)
    db.session.commit()
    auth_token = create_transfer_account_user.encode_auth_token()

    ta1 = create_transfer_account_user.default_transfer_account
    ta2 = create_transfer_account_user_2.default_transfer_account

    ta1.is_approved = True
    ta2.is_approved = True

    ta1.set_balance_offset(1000)
    ta2.set_balance_offset(1000)

    response = test_client.post(
        '/api/v1/me/credit_transfer/',
        headers=dict(
            Authorization=auth_token.decode(),
            Accept='application/json'
        ),
        data=json.dumps(dict(
            is_sending=True,
            transfer_amount=10,
            my_transfer_account_id=ta1.id,
            transfer_account_id=ta2.id
        )),
        content_type='application/json', follow_redirects=True)

    if status == 201:
        a = db.session.query(CreditTransfer)\
            .filter(CreditTransfer.recipient_transfer_account == ta2)\
            .filter(CreditTransfer.transfer_subtype == TransferSubTypeEnum.FEE)\
            .all()
        assert a[0].transfer_type == TransferTypeEnum.PAYMENT
        assert a[0].transfer_amount == amount

    assert response.status_code == status
    db.session.delete(incentive)
