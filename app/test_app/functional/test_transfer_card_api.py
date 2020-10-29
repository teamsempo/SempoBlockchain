from server.models.transfer_card import TransferCard
from server.models.user import User
from server import db
import json
import pytest

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

def test_transfer_card_radius(test_client, init_database, complete_admin_auth_token, authed_sempo_admin_user, create_organisation):
    from server.utils.user import create_transfer_account_user
    # Create cards
    def create_card(public_serial_number, nfc_serial_number):
        return test_client.post('/api/v1/transfer_cards/',
                                    headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                    data=json.dumps({
                                        'public_serial_number': public_serial_number,
                                        'nfc_serial_number': nfc_serial_number
                                    }),
                                    content_type='application/json', follow_redirects=True)
    create_card(123456, 'ABCD1234F')
    create_card(111111, 'AAAA1111A')
    create_card(222222, 'BBBBB111B')
    create_card(333333, 'CCCCC222C')
    create_card(444444, 'DDDDD333D')
    create_card(555555, 'AAAAVVVVV')

    # Create users
    user1 = create_transfer_account_user(first_name='Arthur',
                                        last_name='Read',
                                        phone='+19027191111',
                                        organisation=create_organisation)

    user2 = create_transfer_account_user(first_name='Francine',
                                        last_name='Fresnky',
                                        phone='+19027192222',
                                        organisation=create_organisation)

    user3 = create_transfer_account_user(first_name='Muffy',
                                        last_name='Crosswire',
                                        phone='+19027193333',
                                        organisation=create_organisation)

    user4 = create_transfer_account_user(first_name='Buster',
                                        last_name='Baxter',
                                        phone='+19027194444',
                                        organisation=create_organisation)
    user5 = create_transfer_account_user(first_name='Buster',
                                        last_name='Baxter',
                                        phone='+19027195555',
                                        organisation=create_organisation)

    user6 = create_transfer_account_user(first_name='Binky',
                                        last_name='Barnes',
                                        phone='+19027195455',
                                        organisation=create_organisation)

    # Set locations
    authed_sempo_admin_user.lat = 44.650069
    authed_sempo_admin_user.lng = -63.598865
    authed_sempo_admin_user.location = 'Halifax'

    # Base user (Halifax)
    user1.lat = 44.650069
    user1.lng = -63.598865
    user1.location = 'Halifax'
    # Nearby user (Dartmouth)
    user2.lat = 44.679730
    user2.lng = -63.583979
    user2.location = 'Dartmouth'
    # Kinda far user (Wolfville)
    user3.lat = 45.099418
    user3.lng = -64.323369
    user3.location = 'Wolfville'
    # Very far user (Melbourne)
    user4.lat = -37.874072
    user4.lng = 145.053438
    user4.location = 'Melbourne'
    # Null lat/lng. We want to catch these!
    user5.lat = None
    user5.lng = None
    user5.location = None
    # Incorrect coords, but same location name (Halifax)
    user6.lat = 10.1
    user6.lng = -10.5
    user6.location = 'Halifax'

    db.session.commit()

    # Bind users
    def bind_user(id, serial_number):
        test_client.put(
            f"/api/v1/user/{id}/",
            headers=dict(
                Authorization=complete_admin_auth_token,
                Accept='application/json'
            ),
            json={
                'public_serial_number': serial_number
        })
    bind_user(user1.id, 123456)
    bind_user(user2.id, 111111)
    bind_user(user3.id, 222222)
    bind_user(user4.id, 333333)
    bind_user(user5.id, 444444)
    bind_user(user6.id, 555555)

    # Make sure the distance filters are working!
    distances = [(0, 6), (1, 5), (10, 6), (100, 7), (100000, 8)]
    for distance, length in distances:
        print('DIST')
        print(distance)
        print(length)
        print('DIST')
        # Set card shard distance
        create_organisation.card_shard_distance=distance
        db.session.commit()
        # Get it now!
        response = test_client.get('/api/v1/transfer_cards/',
                               headers=dict(
                                   Authorization=complete_admin_auth_token, Accept='application/json'),
                               follow_redirects=True)
        assert len(response.json['data']['transfer_cards']) == length
    # Check that the sharding flag works (false)
    create_organisation.card_shard_distance=1
    response = test_client.get('/api/v1/transfer_cards/?shard=false',
                           headers=dict(
                               Authorization=complete_admin_auth_token, Accept='application/json'),
                           follow_redirects=True)
    assert len(response.json['data']['transfer_cards']) == 6
    # Check that the sharding flag works (true)
    response = test_client.get('/api/v1/transfer_cards/?shard=true',
                           headers=dict(
                               Authorization=complete_admin_auth_token, Accept='application/json'),
                           follow_redirects=True)
    assert len(response.json['data']['transfer_cards']) == 5
    # Check that it doesn't try to shard when the user doesn't have coords
    authed_sempo_admin_user.lat = None
    authed_sempo_admin_user.lng = None
    response = test_client.get('/api/v1/transfer_cards/',
                           headers=dict(
                               Authorization=complete_admin_auth_token, Accept='application/json'),
                           follow_redirects=True)
    assert len(response.json['data']['transfer_cards']) == 6
