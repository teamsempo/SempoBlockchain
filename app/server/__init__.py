from flask import Flask, request, redirect, render_template, make_response, jsonify, g
import json
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
from celery import Celery
from pusher import Pusher
import boto3
from twilio.rest import Client as TwilioClient
from raven.contrib.flask import  # CHANGE
import messagebird
import africastalking
from datetime import datetime
import redis
import config
import i18n
from eth_utils import to_checksum_address
import sys
import os
from web3 import Web3, HTTPProvider


from server.utils.phone import MessageProcessor

# try:
#     import uwsgi
#     is_running_uwsgi = True
# except ImportError:
#     is_running_uwsgi = False

sys.path.append('../')
import config

dirname = os.path.dirname(__file__)
i18n.load_path.append(os.path.abspath(os.path.join(dirname, 'locale')))
i18n.set('fallback', config.LOCALE_FALLBACK)


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        from decimal import Decimal
        from datetime import datetime
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return str(obj)

        return json.JSONEncoder.default(self, obj)

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config')
    app.config['BASEDIR'] = os.path.abspath(os.path.dirname(__file__))
    # app.config["SQLALCHEMY_ECHO"] = True

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    register_extensions(app)
    register_blueprints(app)

    app.json_encoder = ExtendedJSONEncoder

    return app

def register_extensions(app):
    db.init_app(app)

    basic_auth.init_app(app)

    @app.before_request
    def enable_form_raw_cache():
        # Workaround to allow unparsed request body to be be read from cache
        # This is required to validate a signature on webhooks
        # This MUST go before Sentry integration as sentry triggers form parsing
        if not config.IS_TEST and (
                request.path.startswith('/api/slack/') or request.path.startswith('/api/poli_payments_webhook/')):
            if request.content_length > 1024 * 1024:  # 1mb
                # Payload too large
                return make_response(jsonify({'message': 'Payload too large'})), 413
            request.get_data(parse_form_data=False, cache=True)

    if not config.IS_TEST:
        sentry.init_app(app, dsn=app.config['SENTRY_SERVER_DSN']) # CHANGE https://forum.sentry.io/t/switching-to-sentry-python/4733    
    # limiter.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    celery_app.conf.update(app.config)

    print('celery joined on {} at {}'.format(
        app.config['REDIS_URL'], datetime.utcnow()))


def register_blueprints(app):
    @app.before_request
    def before_request():
        # Celery task list. Tasks are added here so that they can be completed after db commit
        g.celery_tasks = []

        if request.url.startswith('http://') and '.sempo.ai' in request.url:
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

        # if is_running_uwsgi:
        #     print("uswgi connections status is:" + str(uwsgi.is_connected(uwsgi.connection_fd())))
        #
        #     if not uwsgi.is_connected(uwsgi.connection_fd()):
        #         return make_response(jsonify({'message': 'Connection Aborted'})), 401

    @app.after_request
    def after_request(response):
            # Execute any async celery tasks

        if response.status_code < 300 and response.status_code >= 200:
            db.session.commit()

        for task in g.celery_tasks:
            try:
                task.delay()
            except Exception as e:
                sentry.captureException() # CHANGE

        return response

    from .views.index import index_view
    from server.api.auth_api import auth_blueprint
    from server.api.pusher_auth_api import pusher_auth_blueprint
    from server.api.transfer_account_api import transfer_account_blueprint
    from server.api.blockchain_transaction_api import blockchain_transaction_blueprint
    from server.api.geolocation_api import geolocation_blueprint
    from server.api.ip_address_api import ip_address_blueprint
    from server.api.dataset_api import dataset_blueprint
    from server.api.credit_transfer_api import credit_transfer_blueprint
    from server.api.user_api import user_blueprint
    from server.api.kobo_api import user_kobo_blueprint
    from server.me_api import me_blueprint
    from server.api.export_api import export_blueprint
    from server.api.image_uploader_api import image_uploader_blueprint
    from server.api.recognised_face_api import recognised_face_blueprint
    from server.api.filter_api import filter_blueprint
    from server.api.kyc_application_api import kyc_application_blueprint
    from server.api.wyre_api import wyre_blueprint
    from server.api.transfer_usage_api import transfer_usage_blueprint
    from server.api.transfer_card_api import transfer_cards_blueprint
    from server.api.organisation_api import organisation_blueprint
    from server.api.token_api import token_blueprint
    from server.api.slack_api import slack_blueprint
    from server.api.poli_payments_api import poli_payments_blueprint
    from server.api.ussd_api import ussd_blueprint
    from server.api.contract_api import contracts_blueprint
    from server.api.ge_migration_api import ge_migration_blueprint

    versioned_url = '/api/v' + app.config['WEB_VERSION']

    app.register_blueprint(index_view)
    app.register_blueprint(me_blueprint, url_prefix=versioned_url + '/me')
    app.register_blueprint(auth_blueprint, url_prefix=versioned_url)
    app.register_blueprint(pusher_auth_blueprint, url_prefix=versioned_url)
    app.register_blueprint(user_blueprint, url_prefix=versioned_url)
    app.register_blueprint(user_kobo_blueprint, url_prefix=versioned_url)
    app.register_blueprint(transfer_account_blueprint, url_prefix=versioned_url)
    app.register_blueprint(blockchain_transaction_blueprint, url_prefix=versioned_url)
    app.register_blueprint(geolocation_blueprint, url_prefix=versioned_url)
    app.register_blueprint(ip_address_blueprint, url_prefix=versioned_url)
    app.register_blueprint(dataset_blueprint, url_prefix=versioned_url)
    app.register_blueprint(credit_transfer_blueprint, url_prefix=versioned_url)
    app.register_blueprint(export_blueprint, url_prefix=versioned_url)
    app.register_blueprint(image_uploader_blueprint, url_prefix=versioned_url)
    app.register_blueprint(recognised_face_blueprint, url_prefix=versioned_url)
    app.register_blueprint(filter_blueprint, url_prefix=versioned_url)
    app.register_blueprint(kyc_application_blueprint, url_prefix=versioned_url)
    app.register_blueprint(wyre_blueprint, url_prefix=versioned_url)
    app.register_blueprint(transfer_usage_blueprint, url_prefix=versioned_url)
    app.register_blueprint(transfer_cards_blueprint, url_prefix=versioned_url)
    app.register_blueprint(organisation_blueprint, url_prefix=versioned_url)
    app.register_blueprint(token_blueprint, url_prefix=versioned_url)
    app.register_blueprint(slack_blueprint, url_prefix=versioned_url)
    app.register_blueprint(poli_payments_blueprint, url_prefix=versioned_url)
    app.register_blueprint(ussd_blueprint, url_prefix=versioned_url)
    app.register_blueprint(contracts_blueprint, url_prefix=versioned_url)
    app.register_blueprint(ge_migration_blueprint, url_prefix=versioned_url)

    # 404 handled in react
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('index.html'), 404


def encrypt_string(raw_string):
    import base64
    from cryptography.fernet import Fernet
    from eth_utils import keccak

    fernet_encryption_key = base64.b64encode(keccak(text=config.SECRET_KEY))
    cipher_suite = Fernet(fernet_encryption_key)

    return cipher_suite.encrypt(raw_string.encode('utf-8')).decode('utf-8')


db = SQLAlchemy(session_options={
    "expire_on_commit": not config.IS_TEST,
    # enable_baked_queries prevents the before_compile query from getting trapped on
    # organisation change. Shouldn't by default but ¯\_(ツ)_/¯
    # https://docs.sqlalchemy.org/en/13/orm/extensions/baked.html
    "enable_baked_queries": False,
})

basic_auth = BasicAuth()
sentry = Sentry() # CHANGE

# limiter = Limiter(key_func=get_remote_address, default_limits=["20000 per day", "2000 per hour"])

s3 = boto3.client('s3', aws_access_key_id=config.AWS_SES_KEY_ID,
                  aws_secret_access_key=config.AWS_SES_SECRET)

celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')


encrypted_private_key = encrypt_string(config.MASTER_WALLET_PRIVATE_KEY)
prior_tasks = None

red = redis.Redis.from_url(config.REDIS_URL)

pusher_client = Pusher(app_id=config.PUSHER_APP_ID,
                       key=config.PUSHER_KEY,
                       secret=config.PUSHER_SECRET,
                       cluster=config.PUSHER_CLUSTER,
                       ssl=True)

twilio_client = TwilioClient(config.TWILIO_SID, config.TWILIO_TOKEN)
messagebird_client = messagebird.Client(config.MESSAGEBIRD_KEY)
africastalking.initialize(config.AT_USERNAME, config.AT_API_KEY)
africastalking_client = africastalking.SMS

message_processor = MessageProcessor(
    twilio_client=twilio_client, messagebird_client=messagebird_client, africastalking_client=africastalking_client)

from server.utils.blockchain_tasks import BlockchainTasker
bt = BlockchainTasker()

from server.utils.misc_tasks import MiscTasker
mt = MiscTasker()

from server.utils.ussd.ussd_tasks import UssdTasker
ussd_tasker = UssdTasker()

ge_w3 = Web3(HTTPProvider(config.GE_HTTP_PROVIDER))


