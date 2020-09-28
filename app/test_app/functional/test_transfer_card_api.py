from server.models.transfer_card import TransferCard
import json

def test_transfer_card_api(test_client, init_database, complete_admin_auth_token, create_transfer_account_user):

    # Test regular load of card
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': 123456,
                                    'nfc_serial_number': 'ABCD1234F'
                                }),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 201

    # Ensure duplicated public_serial_number fails, even if provided as string
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': '123456',
                                    'nfc_serial_number': '123DEEF'
                                }),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400

    # Ensure duplicated nfc_id fails, even if nfc is lowercase
    response = test_client.post('/api/v1/transfer_cards/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps({
                                    'public_serial_number': '22222',
                                    'nfc_serial_number': 'abcd1234F'
                                }),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400

    # Make sure db reflects what we'd expect
    cards = TransferCard.query.all()

    assert len(cards) == 1
    card = cards[0]
    assert card.public_serial_number == '123456'
    assert card.nfc_serial_number == 'ABCD1234F'

    # Now try a get of the data
    response = test_client.get('/api/v1/transfer_cards/',
                               headers=dict(
                                   Authorization=complete_admin_auth_token, Accept='application/json'),
                               follow_redirects=True)

    assert response.status_code == 200
    # Should not return any cards, since defaults to not returning cards bound to a transfer_account
    assert len(response.json['data']['transfer_cards']) == 0

    # Now try a get of the data, getting ALL cards, not just ones that are bound
    response = test_client.get('/api/v1/transfer_cards/?only_bound=false',
                               headers=dict(
                                   Authorization=complete_admin_auth_token, Accept='application/json'),
                               follow_redirects=True)

    assert response.status_code == 200

    card_json = response.json['data']['transfer_cards'][0]
    assert card_json['nfc_serial_number'] == 'ABCD1234F'
    assert card_json['public_serial_number'] == '123456'

    # Now bind to a user
    test_client.put(
        f"/api/v1/user/{create_transfer_account_user.id}/",
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'public_serial_number': '123456'
    })

    response = test_client.get('/api/v1/transfer_cards/',
                               headers=dict(
                                   Authorization=complete_admin_auth_token, Accept='application/json'),
                               follow_redirects=True)

    assert response.status_code == 200

    # Should now return our card
    card_json = response.json['data']['transfer_cards'][0]
    assert card_json['nfc_serial_number'] == 'ABCD1234F'
    assert card_json['public_serial_number'] == '123456'



