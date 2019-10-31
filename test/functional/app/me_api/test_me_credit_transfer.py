
def test_get_me_credit_transfer_api(test_client, create_credit_transfer, create_transfer_account_user):
    """
    GIVEN a Flask application
    WHEN '/api/me/credit_transfer/' is requested (GET)
    THEN check a list of credit transfers is returned
    """
    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    response = test_client.get('/api/me/credit_transfer/',
                               headers=dict(Authorization=auth_token.decode(), Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 201
    assert response.json['data']['credit_transfers'][0]['id'] is create_credit_transfer.id


# @pytest.mark.parametrize('transfer_account_id,nfc_id,public_identifier,is_sending', [
#     (1, None, None, True),  # tests online transfers
#     (None, 'randomNFCid123', None, False)  # tests online nfc transfers
# ])
# # todo- test nfc transfer, offline qr transfer, online qr transfer, send to public identifier
# def test_post_me_credit_transfer_api(test_client, create_transfer_account_user, new_disbursement, transfer_account_id, nfc_id, public_identifier, is_sending):
#     """
#     GIVEN a Flask application
#     WHEN '/api/me/credit_transfer/' is posted (POST) with amount, transfer_account_id, is_sending
#     THEN check a transfer is created
#     """
#     # create_transfer_account_user.transfer_account.balance = 100
#     disbursement = new_disbursement
#     create_transfer_account_user.nfc_serial_number = nfc_id
#
#     create_transfer_account_user.is_activated = True
#     auth_token = create_transfer_account_user.encode_auth_token()
#
    # response = test_client.post('/api/me/credit_transfer/',
    #                             headers=dict(Authorization=auth_token.decode(), Accept='application/json', ContentType='application/json'),
    #                             data=json.dumps(dict(
    #                                     transfer_amount=100,
    #                                     transfer_account_id=transfer_account_id,
    #                                     transfer_random_key=None,
    #                                     qr_data=None,
    #                                     nfc_id=nfc_id,
    #                                     is_sending=is_sending,
    #                                     public_identifier=public_identifier,
    #                                 )),
    #                             content_type='application/json', follow_redirects=True)
#     assert response.status_code == 201

# def test_post_me_credit_transfer_api_offline_qr(test_client, create_transfer_account_user):
#     """
#     GIVEN a Flask application
#     WHEN '/api/me/credit_transfer/' is posted (POST) with qr_data
#     THEN check a transfer is created
#     """
#     import hashlib
#
#     hashlib.sha256(string_to_hash.encode()).hexdigest()
#
#     create_transfer_account_user.transfer_account.balance = 100
#     create_transfer_account_user.is_activated = True
#     auth_token = create_transfer_account_user.encode_auth_token()
#     response = test_client.post('/api/me/credit_transfer/',
#                                 headers=dict(Authorization=auth_token.decode(), Accept='application/json',
#                                              ContentType='application/json'),
#                                 data=json.dumps(dict(
#                                     transfer_amount=100,
#                                     transfer_account_id=transfer_account_id,
#                                     transfer_random_key=None,
#                                     qr_data='100-1-',
#                                     nfc_id=nfc_id,
#                                     is_sending=is_sending,
#                                     public_identifier=public_identifier,
#                                 )),
#                                 content_type='application/json', follow_redirects=True)
#     assert response.status_code == 201
