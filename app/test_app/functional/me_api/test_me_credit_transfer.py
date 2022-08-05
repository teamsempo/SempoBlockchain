import pytest, json, base64, config
from uuid import uuid4
from server import db
from server.models.credit_transfer import CreditTransfer

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


def test_create_me_credit_transfer_api(
        test_client,
        create_transfer_account_user,
        create_transfer_account_user_2,
        complete_admin_auth_token
):

    """
    GIVEN a Flask application
    WHEN '/api/me/credit_transfer/' is requested (POST) with transfer card data
    THEN a credit transfer is created
    """
    # Setup test accounts
    ta1 = create_transfer_account_user.default_transfer_account
    ta2 = create_transfer_account_user_2.default_transfer_account

    ta1.is_approved = True
    ta2.is_approved = True

    create_transfer_account_user.is_activated = True
    create_transfer_account_user_2.is_activated = True

    ta1.set_balance_offset(1000)
    ta2.set_balance_offset(1000)

    # Create transfer card for ta2, and bind it to them
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': '222222',
                                    'nfc_serial_number': 'FFFFFFFFF'
                                }),
                                content_type='application/json', follow_redirects=True)
        
    response = test_client.put(
                f"/api/v1/user/{create_transfer_account_user_2.id}/",
                headers=dict(
                    Authorization=complete_admin_auth_token,
                    Accept='application/json'
                ),
                json={
                    'public_serial_number': '222222'
            })
        
    # Make the transfer
    transfer_payload = {
        'nfc_id': 'FFFFFFFFF',
        'qr_id': None,
        'transfer_amount': 10,
        'transfer_use': [],
        'my_transfer_account_id': create_transfer_account_user.transfer_account.id,
        'uuid': str(uuid4()),
        'created': "2022-08-17T14:48:00.000Z",
        'inCache': True
    }
    response = test_client.post(
        '/api/v1/me/credit_transfer/',
        headers=dict(
            Authorization=create_transfer_account_user.encode_auth_token().decode(),
            Accept='application/json'
        ),
        data=json.dumps(transfer_payload),
        content_type='application/json', follow_redirects=True)

    # Make sure the transfer actually worked
    assert response.status_code == 201
    new_transfer_id = response.json['data']['credit_transfer']['id']
    credit_transfer = db.session.query(CreditTransfer).filter(CreditTransfer.id == new_transfer_id).first()
    assert credit_transfer.transfer_amount == 10
    assert credit_transfer.recipient_transfer_account_id == create_transfer_account_user.default_transfer_account.id
    assert credit_transfer.sender_transfer_account_id == create_transfer_account_user_2.default_transfer_account.id
    
    # Make sure the transfer card usage was stored and all the joins work correctly  
    card_usage_object = credit_transfer.transfer_card_state 
    assert card_usage_object.transfer_card.public_serial_number == '222222'
    assert card_usage_object.transfer_card.transfer_card_states == [card_usage_object]
    
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
