from server.models.transfer_card import TransferCard
import json, pytest

def test_transfer_card_api(test_client, init_database, complete_admin_auth_token):

    # Test regular load of card
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': '123456',
                                    'nfc_serial_number': 'abcd1234f'
                                }),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 201

    # Ensure duplicated public_serial_number fails
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': '123456',
                                    'nfc_serial_number': '123deef'
                                }),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400

    # Ensure duplicated nfc_id fails
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': '22222',
                                    'nfc_serial_number': 'abcd1234f'
                                }),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400

    # Make sure db reflects what we'd expect
    cards = TransferCard.query.all()

    assert len(cards) == 1
    card = cards[0]
    assert card.public_serial_number == '123456'
    assert card.nfc_serial_number == 'abcd1234f'

    # Now try a get of the data

    response = test_client.get('/api/v1/transfer_usage/',
                               args=
                               headers=dict(
                                   Authorization=complete_admin_auth_token, Accept='application/json'),
                               follow_redirects=True)

    assert response.status_code == 200
    assert isinstance(response.json['data']['transfer_usages'], list)

    # Ensure that the posting a duplicate transfer ussage results in a 400
    response = test_client.post('/api/v1/transfer_usage/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(name=name, icon=icon, translations=translations)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400
