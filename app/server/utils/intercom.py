import hashlib, hmac
from flask import current_app


def create_intercom_secret(user_id, device_type):
    """
    Function to generate an intercom secret using HMAC for identity verification for customer support.

    :param user_id: Sempo UserID to generate a unique hash.
    :param device_type: Web, Android or iOS
    :return:
    """
    if device_type == 'WEB':
        secret = current_app.config['INTERCOM_WEB_SECRET']
    elif device_type == 'ANDROID':
        secret = current_app.config['INTERCOM_ANDROID_SECRET']
    else:
        return Exception('No device_type provided')

    secret_bytes = secret.encode('ascii')
    id_bytes = str(user_id).encode('ascii')
    result = hmac.new(secret_bytes, id_bytes, hashlib.sha256).hexdigest()

    return result
