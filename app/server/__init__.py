from flask import Flask, request, redirect, render_template, make_response, jsonify, g
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
from pusher import Pusher
import boto3
from twilio.rest import Client as TwilioClient
from raven.contrib.flask import Sentry
import messagebird
from datetime import datetime
import redis
import config

import sys, os

# try:
#     import uwsgi
#     is_running_uwsgi = True
# except ImportError:
#     is_running_uwsgi = False

sys.path.append('../')

db = SQLAlchemy(session_options={"expire_on_commit": not config.IS_TEST})
basic_auth = BasicAuth()
sentry = Sentry()

# limiter = Limiter(key_func=get_remote_address, default_limits=["20000 per day", "2000 per hour"])

s3 = boto3.client('s3', aws_access_key_id=config.AWS_SES_KEY_ID,
                  aws_secret_access_key=config.AWS_SES_SECRET)

messagebird_client = messagebird.Client(config.MESSAGEBIRD_KEY)

celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

red = redis.Redis.from_url(config.REDIS_URL)

pusher_client = Pusher(app_id=config.PUSHER_APP_ID,
                       key=config.PUSHER_KEY,
                       secret=config.PUSHER_SECRET,
                       cluster=config.PUSHER_CLUSTER,
                       ssl=True)

twilio_client = TwilioClient(config.TWILIO_SID, config.TWILIO_TOKEN)


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

    return app


def register_extensions(app):
    db.init_app(app)

    basic_auth.init_app(app)

    if not config.IS_TEST:
        sentry.init_app(app, dsn=app.config['SENTRY_SERVER_DSN'])
    # limiter.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    celery_app.conf.update(app.config)

    print('celery joined on {} at {}'.format(app.config['REDIS_URL'], datetime.utcnow()))

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
        for task in g.celery_tasks:
            try:
                task.delay()
            except Exception as e:
                sentry.captureException()

        return response

    from .views.index import index_view
    from server.api.auth_api import auth_blueprint
    from server.api.pusher_auth_api import pusher_auth_blueprint
    from server.api.transfer_account_api import transfer_account_blueprint
    from server.api.whatsapp_api import whatsapp_blueprint
    from server.api.blockchain_transaction_api import blockchain_transaction_blueprint
    from server.api.geolocation_api import geolocation_blueprint
    from server.api.ip_address_api import ip_address_blueprint
    from server.api.dataset_api import dataset_blueprint
    from server.api.credit_transfer_api import credit_transfer_blueprint
    from server.api.sms_api import sms_blueprint
    from server.api.user_api import user_blueprint
    from server.api.me_api import me_blueprint
    from server.api.export_api import export_blueprint
    from server.api.image_uploader_api import image_uploader_blueprint
    from server.api.recognised_face_api import recognised_face_blueprint
    from server.api.filter_api import filter_blueprint
    from server.api.kyc_application_api import kyc_application_blueprint
    from server.api.wyre_api import wyre_blueprint
    from server.api.transfer_usage_api import transfer_usage_blueprint
    from server.api.transfer_card_api import transfer_cards_blueprint
    from server.api.blockchain_address_api import blockchain_address_blueprint
    from server.api.organisation_api import organisation_blueprint
    from server.api.token_api import token_blueprint

    app.register_blueprint(index_view)
    app.register_blueprint(me_blueprint, url_prefix='/api/me')
    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(pusher_auth_blueprint, url_prefix='/api')
    app.register_blueprint(user_blueprint, url_prefix='/api')
    app.register_blueprint(transfer_account_blueprint, url_prefix='/api')
    app.register_blueprint(whatsapp_blueprint, url_prefix='/api')
    app.register_blueprint(blockchain_transaction_blueprint, url_prefix='/api')
    app.register_blueprint(geolocation_blueprint, url_prefix='/api')
    app.register_blueprint(ip_address_blueprint, url_prefix='/api')
    app.register_blueprint(dataset_blueprint, url_prefix='/api')
    app.register_blueprint(credit_transfer_blueprint, url_prefix='/api')
    app.register_blueprint(sms_blueprint, url_prefix='/api')
    app.register_blueprint(export_blueprint, url_prefix='/api')
    app.register_blueprint(image_uploader_blueprint, url_prefix='/api')
    app.register_blueprint(recognised_face_blueprint, url_prefix='/api')
    app.register_blueprint(kyc_application_blueprint, url_prefix='/api')
    app.register_blueprint(wyre_blueprint, url_prefix='/api')
    app.register_blueprint(transfer_usage_blueprint, url_prefix='/api')
    app.register_blueprint(transfer_cards_blueprint, url_prefix='/api')
    app.register_blueprint(blockchain_address_blueprint, url_prefix='/api')
    app.register_blueprint(organisation_blueprint, url_prefix='/api')
    app.register_blueprint(token_blueprint, url_prefix='/api')

    # 404 handled in react
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('index.html'), 404
