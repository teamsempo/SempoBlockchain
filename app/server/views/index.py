# -*- coding: utf-8 -*-
from flask import render_template, Blueprint, current_app, g
import config
from server.utils.auth import requires_auth
from server.utils.multi_chain import get_chain
import glob, os
from pathlib import Path

index_view = Blueprint('index', __name__,
                        template_folder='templates')


def get_js_bundle_filename(search_string):
    bundle_directory = os.path.join(current_app.config['BASEDIR'], "static/javascript/dist")
    globs = glob.glob(os.path.join(bundle_directory, search_string))

    # We need the most recent file because webpack doesn't clean when dev-ing
    latest_file = max(globs, key=os.path.getctime)

    return Path(latest_file).name

@index_view.route('/', defaults={'path': ''})
@index_view.route('/<path:path>')
def catch_all(path):
    return render_template(
        'index.html',
        js_bundle_main=get_js_bundle_filename('main.bundle.*.js'),
        js_bundle_vendor=get_js_bundle_filename('vendors~main.bundle.*.js'),
        chain=get_chain(),
    )

@index_view.route('/whatsapp-sync/')
@requires_auth(allowed_basic_auth_types=('internal',))
def WhatsApp_sync():
    return render_template('WhatsAppQR.html', qr_code = whatsapp_q.get_info('whatsApp_qr_code').get('data'), status = whatsapp_q.get_info('whatsApp_status'))