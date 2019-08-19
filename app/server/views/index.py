# -*- coding: utf-8 -*-
from flask import render_template, Blueprint, current_app
from server import basic_auth, celery_app
import glob, os
from pathlib import Path
from celery import signature

index_view = Blueprint('index', __name__,
                        template_folder='templates')

def get_js_bundle_filename():
    bundle_directory = os.path.join(current_app.config['BASEDIR'], "static/javascript/dist")
    globs = glob.glob(os.path.join(bundle_directory, 'main.bundle.*.js'))

    # We need the most recent file because webpack doesn't clean when dev-ing
    latest_file = max(globs, key=os.path.getctime)

    return Path(latest_file).name

@index_view.route('/')
def index():

    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/<accounts>')
def accounts(accounts):
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/accounts/<account_id>')
def single_account(account_id):
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/users/<user_id>')
def single_user(user_id):
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/upload')
def upload():
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

# @index_view.route('/<account_type>/upload/')
# def upload(account_type):
#     return render_template('index.html')

@index_view.route('/vendors')
def vendor():
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/deprecatedVendor')
def deprecatedVendor():
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/settings/<subroute>')
def settings(subroute):
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/activate-account/')
def activate_account():
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/reset-password/')
def reset_password():
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/login/<subroute>')
def login(subroute):
    return render_template('index.html', js_bundle_main = get_js_bundle_filename())

@index_view.route('/whatsapp-sync/')
@basic_auth.required
def WhatsApp_sync():
    return render_template('WhatsAppQR.html', qr_code = whatsapp_q.get_info('whatsApp_qr_code').get('data'), status = whatsapp_q.get_info('whatsApp_status'))