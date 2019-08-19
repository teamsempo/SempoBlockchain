import hashlib, hmac
from flask import current_app


def create_intercom_android_secret(user_id):
    secret_bytes = current_app.config['INTERCOM_ANDROID_SECRET'].encode('ascii')
    id_bytes = str(user_id).encode('ascii')
    result = hmac.new(secret_bytes, id_bytes, hashlib.sha256).hexdigest()
    return result
