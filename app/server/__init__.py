from typing import Callable, Union
from flask import Flask, request, redirect, render_template, make_response, jsonify, g
import json
from flask_executor import Executor

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from flask_basicauth import BasicAuth
from celery import Celery
from pusher import Pusher
import boto3
from twilio.rest import Client as TwilioClient
import sentry_sdk
from sentry_sdk import configure_scope
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

import messagebird
import africastalking
from datetime import datetime
import redis
import i18n
from eth_utils import to_checksum_address
import sys
import os
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from server.sempo_types import DeferredJobList

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

def create_app(skip_create_filters = False):
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

    if not skip_create_filters:
        # On app start, we send token addresses to the worker
        try:
            with app.app_context():
                from server.utils.synchronization_filter import add_transaction_filter
                from server.models.token import Token
                tokens = db.session.query(Token)
                for t in tokens:
                    print(f'Creating transaction filter for {t.address}')
                    if t.address:
                        add_transaction_filter(t.address, 'ERC20', None, 'TRANSFER', decimals = t.decimals, block_epoch = config.THIRD_PARTY_SYNC_EPOCH)
        except:
            print('Unable to automatically create filters')
    return app


def register_extensions(app):
    db.init_app(app)
    executor.init_app(app)
    basic_auth.init_app(app)

    @app.before_request
    def enable_form_raw_cache():
        # Workaround to allow unparsed request body to be be read from cache
        # This is required to validate a signature on webhooks
        # This MUST go before Sentry integration as sentry triggers form parsing
        if not config.IS_TEST and (
                request.path.startswith('/api/v1/slack/') or request.path.startswith('/api/v1/poli_payments_webhook/')):
            if request.content_length > 1024 * 1024:  # 1mb
                # Payload too large
                return make_response(jsonify({'message': 'Payload too large'})), 413
            request.get_data(parse_form_data=False, cache=True)

    # limiter.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    celery_app.conf.update(app.config)
    if not config.IS_TEST:
        sentry_sdk.init(
            app.config['SENTRY_SERVER_DSN'], 
            integrations=[FlaskIntegration(), SqlalchemyIntegration(), RedisIntegration()], 
            release=config.VERSION
        )
        with configure_scope() as scope:
            scope.set_tag("domain", config.APP_HOST)

    print('celery joined on {} at {}'.format(
        app.config['REDIS_URL'], datetime.utcnow()))


def register_blueprints(app):
    @app.before_request
    def before_request():
        # Celery task list. Tasks are added here so that they can be completed after db commit
        g.pending_transactions = []
        g.deferred_jobs: DeferredJobList = []
        g.is_after_request = False

    @app.after_request
    def after_request(response):
        def _prepare_and_execute_deferred_tasks():
            g.is_after_request = True
            if g.deferred_jobs:
                for job, args, kwargs in g.deferred_jobs:
                    job.submit(*args, **kwargs)
            from server.utils.executor import after_deferred_jobs
            after_deferred_jobs()

        if response.status_code < 300 and response.status_code >= 200:
            db.session.commit()
        if config.IS_TEST:
            _prepare_and_execute_deferred_tasks()
        else:
            from flask.globals import _app_ctx_stack
            appctx = _app_ctx_stack.top
            @response.call_on_close
            def on_close():
                with appctx:
                    from server.models.organisation import Organisation
                    from server.models.user import User
                    if g and g.get('active_organisation'):
                        g.active_organisation = db.session.query(Organisation).filter(Organisation.id == g.active_organisation.id).first() 
                        db.session.merge(g.active_organisation)
                        db.session.merge(g.active_organisation.token)
                    if g and g.get('user'):
                        g.user = db.session.query(User).filter(User.id == g.user.id).first() 
                        db.session.merge(g.user)
                    _prepare_and_execute_deferred_tasks()
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
    from server.api.synchronization_filter_api import synchronization_filter_blueprint
    from server.api.blockchain_taskable_api import blockchain_taskable_blueprint
    from server.api.metrics_api import metrics_blueprint
    from server.api.mock_data_api import mock_data_blueprint
    from server.api.attribute_map_api import attribute_map_blueprint
    from server.api.vendor_payout_api import vendor_payout
    from server.api.disbursement_api import disbursement_blueprint 
    from server.api.async_api import async_blueprint 
    from server.api.master_wallet_api import master_wallet_blueprint 

    versioned_url = '/api/v1'

    app.register_blueprint(index_view)
    app.register_blueprint(me_blueprint, url_prefix=versioned_url + '/me')
    app.register_blueprint(auth_blueprint, url_prefix=versioned_url)
    app.register_blueprint(pusher_auth_blueprint, url_prefix=versioned_url)
    app.register_blueprint(user_blueprint, url_prefix=versioned_url)
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
    app.register_blueprint(synchronization_filter_blueprint, url_prefix=versioned_url)
    app.register_blueprint(blockchain_taskable_blueprint, url_prefix=versioned_url)
    app.register_blueprint(metrics_blueprint, url_prefix=versioned_url)
    app.register_blueprint(mock_data_blueprint, url_prefix=versioned_url)
    app.register_blueprint(attribute_map_blueprint, url_prefix=versioned_url)
    app.register_blueprint(vendor_payout, url_prefix=versioned_url)
    app.register_blueprint(disbursement_blueprint, url_prefix=versioned_url)
    app.register_blueprint(async_blueprint, url_prefix=versioned_url)
    app.register_blueprint(master_wallet_blueprint, url_prefix=versioned_url)

    # 404 handled in react
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('index.html'), 404


def none_if_exception(f: Callable) -> Union[object, None]:
    """
    A helper function for when you're lacking configs for external packages.
    Use a partial or lambda to delay execution of f.
    :param f: a callable object instantiator
    :return: an initialised package object, or None
    """
    try:
        return f()
    except:
        return None

def encrypt_string(raw_string):
    import base64
    from cryptography.fernet import Fernet
    from eth_utils import keccak

    fernet_encryption_key = base64.b64encode(keccak(text=config.SECRET_KEY))
    cipher_suite = Fernet(fernet_encryption_key)

    return cipher_suite.encrypt(raw_string.encode('utf-8')).decode('utf-8')


class AppQuery(BaseQuery):
    """
    We subclass the base Query to ensure that the `filter_by_org` event listener only applies to the app.
    Otherwise, SQLAlchemy will apply it to the base 'Query' class.
    In this case if `filter_by_org` happens to be imported by eg the eth_worker during tests
    (pytest will do this if you run both test sets simultaneously), the lister will be applied to eth_worker
    SQLAlachemy queries
    """
    pass


db = SQLAlchemy(
    query_class=AppQuery,
    engine_options={
        'pool_pre_ping': True
    },
    session_options={
        "expire_on_commit": False,
        "enable_baked_queries": False
        # enable_baked_queries prevents the filter_by_org query from getting trapped on
        # organisation change. Shouldn't by default but ¯\_(ツ)_/¯
        # https://docs.sqlalchemy.org/en/13/orm/extensions/baked.html
    }
)

basic_auth = BasicAuth()
executor = Executor()

# limiter = Limiter(key_func=get_remote_address, default_limits=["20000 per day", "2000 per hour"])

s3 = boto3.client('s3', aws_access_key_id=config.AWS_SES_KEY_ID,
                  aws_secret_access_key=config.AWS_SES_SECRET)

celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

prior_tasks = None

red = redis.Redis.from_url(config.REDIS_URL)

try:
    pusher_client = Pusher(app_id=config.PUSHER_APP_ID,
                           key=config.PUSHER_KEY,
                           secret=config.PUSHER_SECRET,
                           cluster=config.PUSHER_CLUSTER,
                           ssl=True)
except:
    class PusherMock(object):
        def authenticate(self, *args, **kwargs):
            return ''
        def trigger(self, *args, **kwargs):
            pass
        def trigger_batch(self, *args, **kwargs):
            pass

    pusher_client = PusherMock()


def africas_talking_launcher():
    africastalking.initialize(config.AT_USERNAME, config.AT_API_KEY)
    return africastalking.SMS


twilio_client = none_if_exception(lambda: TwilioClient(config.TWILIO_SID, config.TWILIO_TOKEN))
messagebird_client = none_if_exception(lambda: messagebird.Client(config.MESSAGEBIRD_KEY))
africastalking_client = none_if_exception(africas_talking_launcher)

from server.utils.blockchain_tasks import BlockchainTasker
bt = BlockchainTasker()

from server.utils.misc_tasks import MiscTasker
mt = MiscTasker()

from server.utils.ussd.ussd_tasks import UssdTasker
ussd_tasker = UssdTasker()

if config.VERIFY_THIRD_PARTY_SYNC:
    print('Launching transaction sync checker scheduler')
    try:
        from server.utils.credit_transfer import check_recent_transaction_sync_status
        interval_time = config.THIRD_PARTY_SYNC_ERROR_DETECTION_INTERVAL
        time_to_error = config.THIRD_PARTY_SYNC_ERROR_DETECTION_GRACE_PERIOD
        scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
        scheduler.add_job(func=check_recent_transaction_sync_status, trigger="interval", seconds=interval_time, args=[interval_time, time_to_error])
        scheduler.start()
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
    except:
            print('Unable to launch scheduler')
