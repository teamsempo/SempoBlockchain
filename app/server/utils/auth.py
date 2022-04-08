import time
from functools import wraps, partial
from flask import request, g, make_response, jsonify, current_app
from server import db
from server.constants import DENOMINATION_DICT
from server.models.currency_conversion import CurrencyConversion
from server.models.transfer_account import TransferAccount
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.models.ip_address import IpAddress
from server.models.organisation import Organisation
from server.utils.access_control import AccessControl
import config, hmac, hashlib, json
from typing import Optional, Tuple, Dict

from server.utils.blockchain_transaction import get_usd_to_satoshi_rate
from server.utils.feedback import request_feedback_questions
from server.utils.intercom import create_intercom_secret
from server.utils.misc import decrypt_string
from server.schemas import organisation_schema, organisations_schema

def get_complete_auth_token(user):
    auth_token = user.encode_auth_token().decode()
    tfa_token = user.encode_TFA_token(9999).decode()
    return auth_token + '|' + tfa_token

def show_all(f):
    """
    Decorator for endpoints to tell SQLAlchemy not to filter any query by organisation ID
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        g.show_all = True
        return f(*args, **kwargs)
    return wrapper

def multi_org(f):
    """
    Decorator for endpoints to tell SQLAlchemy that it's dealing with a multi-org friendly endpoint
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        g.multi_org = True
        return f(*args, **kwargs)
    return wrapper


def requires_auth(f=None,
                  allowed_roles: Optional[Dict]=None,
                  allowed_basic_auth_types: Optional[Tuple]=None,  # currently 'external' or 'internal'
                  ignore_tfa_requirement: bool=False,
                  allow_query_string_auth: bool=False):

    allowed_roles = allowed_roles or dict()
    allowed_basic_auth_types = allowed_basic_auth_types or tuple()

    if not isinstance(allowed_basic_auth_types, tuple):
        # Because 'tern' in ('internal') >> True
        # Where as 'tern' in ('internal',) >> False
        raise RuntimeError('allowed_basic_auth_types must be a tuple')

    if f is None:
        return partial(requires_auth,
                       allowed_roles=allowed_roles,
                       allowed_basic_auth_types=allowed_basic_auth_types,
                       ignore_tfa_requirement=ignore_tfa_requirement,
                       allow_query_string_auth=allow_query_string_auth)

    @wraps(f)
    def wrapper(*args, **kwargs):

        # ----- FIRST GET AUTH VALUES -----

        # Query string auth needs to be explicity allowed for an endpoint since it can lead to security vulnerabilities
        # if used incorrectly by the client (for example credentials getting logged by website trackers).
        # We get credentials with it first, meaning any values will be overwritten by a present header auth
        if allow_query_string_auth:
            username = request.args.get('username', None)
            password = request.args.get('password', None)

            auth_token = request.args.get('auth_token', None)
            tfa_token = request.args.get('tfa_token', None)
        else:
            username = None
            password = None
            auth_token = None
            tfa_token = None

        # Next get basic auth, which we parse using flask's built-in process, if present overwriting query string values
        auth = request.authorization
        if auth and auth.type == 'basic':
            username = auth.username or username
            password = auth.password or password

        # Lastly, get any custom set Sempo auth headers, if present overwriting query string values
        auth_header = request.headers.get('Authorization')
        if auth_header:
            split_header = auth_header.split("|")
            auth_token = split_header[0]
            try:
                tfa_token = split_header[1]
            except IndexError:
                # Auth header does not contain a TFA token, try getting it from explicit header instead
                # (dev convenience)
                tfa_token = request.headers.get('TFA_Authorization') or tfa_token

        # ----- THEN ATTEMPT AUTHORIZATION -----

        # If username as password attempt basic auth
        if username and password:


            # Make sure basic auth is allowed
            if len(allowed_basic_auth_types) == 0:
                response_object = {
                    'message': 'basic auth not allowed'
                }
                return make_response(jsonify(response_object)), 401


            # Try to find a matching password and auth type for the username, checking orgs first and then config
            # Check if username belongs to an org
            org = Organisation.query.filter_by(external_auth_username = username).first()
            if org:
                auth_type = 'external'
                required_password = org.external_auth_password

            # Otherwise, check if it is one of the allowed BASIC_AUTH_CREDENTIALS
            else:
                try:
                    (required_password, auth_type) = current_app.config['BASIC_AUTH_CREDENTIALS'][username]
                except KeyError:
                    required_password = None
                    auth_type = None

            g.auth_type = auth_type
            if required_password is None or required_password != password:
                response_object = {
                    'message': 'invalid basic auth username or password'
                }
                return make_response(jsonify(response_object)), 401

            if (auth_type not in allowed_basic_auth_types) or (auth_type is None):
                response_object = {
                    'message': 'Basic Auth type is {}. Must be: {}'.format(auth_type, allowed_basic_auth_types)
                }
                return make_response(jsonify(response_object)), 401

            g.active_organisation = org

            return f(*args, **kwargs)

        if auth_token:

            resp = User.decode_auth_token(auth_token)

            if not isinstance(resp, str):

                    user = User.query.filter_by(id=resp['id']).execution_options(show_all=True).first()

                    if not user:
                        response_object = {
                            'status': 'fail',
                            'message': 'user not found'
                        }
                        return make_response(jsonify(response_object)), 401

                    if not user.is_activated:
                        response_object = {
                            'status': 'fail',
                            'message': 'user not activated'
                        }
                        return make_response(jsonify(response_object)), 401

                    if user.is_disabled:
                        response_object = {
                            'status': 'fail',
                            'message': 'user has been disabled'
                        }
                        return make_response(jsonify(response_object)), 401

                    tfa_response_object = tfa_logic(user, tfa_token, ignore_tfa_requirement)
                    if tfa_response_object:
                        return make_response(jsonify(tfa_response_object)), 401

                    if len(allowed_roles) > 0:
                        held_roles = resp.get('roles', {})

                        if not AccessControl.has_suffient_role(held_roles, allowed_roles):
                            response_object = {
                                'message': 'user does not have any of the allowed roles: ' + str(allowed_roles),
                            }
                            return make_response(jsonify(response_object)), 403

                    # ----- AUTH PASSED, DO FINAL SETUP -----

                    g.user = user
                    g.member_organisations = [org.id for org in user.organisations]
                    try:
                        g.active_organisation = None

                        # First try to set the active org from the query
                        query_org = request.args.get('org', None)
                        if query_org is not None:
                            try:
                                query_org = int(query_org)
                                if query_org in g.member_organisations:
                                    g.active_organisation = Organisation.query.get(query_org)
                            except ValueError:
                                pass

                        # Then get the fallback organisation
                        if g.active_organisation is None:
                            g.active_organisation = user.fallback_active_organisation()

                        # Check for query_organisations as well. These are stored in g and used for operations which
                        # are allowed to be run against multiple orgs. Submitted as a CSV
                        # E.g. GET metrics, user list, transfer list should be gettable with ?query_organisations=1,2,3
                        query_organisations = request.args.get('query_organisations', None)
                        if query_organisations:
                            g.query_organisations = []
                            try:
                                query_organisations = [int(q) for q in query_organisations.split(',')]
                                if set(query_organisations).issubset(set(g.member_organisations)):
                                    g.query_organisations = query_organisations
                            except ValueError:
                                pass


                    except NotImplementedError:
                        g.active_organisation = None

                    check_ip(user)

                    # updates the validated user last seen timestamp
                    user.update_last_seen_ts()

                    #This is the point where you've made it through ok and you can return the top method
                    return f(*args, **kwargs)

            response_object = {
                'status': 'fail',
                'message': resp
            }
            return make_response(jsonify(response_object)), 401

        response_object = {
            'status': 'fail',
            'message': 'Provide a valid auth token.'
        }
        return make_response(jsonify(response_object)), 401

    return wrapper


def tfa_logic(user, tfa_token, ignore_tfa_requirement=False):

    if (user.is_TFA_required() or user.TFA_enabled) and not ignore_tfa_requirement:
        if not user.TFA_enabled:
            # Go down this path if user is yet to set up TFA
            tfa_url = user.tfa_url

            db.session.commit()

            response_object = {
                'tfa_url': tfa_url,
                'message': 'User must setup two factor authentication'
            }

            return response_object

        # Otherwise, check TFA
        if tfa_token is None:
            response_object = {
                'tfa_failure': True,
                'message': 'TFA token required, none supplied'
            }
            return response_object

        tfa_response = User.decode_auth_token(tfa_token, 'TFA')

        if isinstance(tfa_response, str):
            # User doesn't have valid TFA token
            response_object = {
                'tfa_failure': True,
                'message': tfa_response
            }
            return response_object

        if tfa_response.get("token_type") != "TFA":
            # Ensure the TFA token was generated by encode_TFA_token
            response_object = {
                'tfa_failure': True,
                'message': 'Invalid TFA response'
            }

            return response_object

        if tfa_response.get("id") != user.id:
            # User doesn't has valid TFA token BUT it's not theirs
            response_object = {
                'tfa_failure': True,
                'message': 'Invalid User ID in TFA response'
            }

            return response_object

    return None


def check_ip(user):
    real_ip_address = request.remote_addr
    if real_ip_address is not None and not IpAddress.check_user_ips(user, real_ip_address):
        # IP exists in request and is not already saved
        new_ip = IpAddress(ip=real_ip_address)
        new_ip.user = user
        db.session.add(new_ip)


def verify_slack_requests(f=None):
    """
    Verify the request signature of the request sent from Slack
    Generate a new hash using the app's signing secret and request data
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        signature = request.headers['X-Slack-Signature']
        timestamp = request.headers['X-Slack-Request-Timestamp']
        data = request.data.decode('utf-8')
        # data = urllib.parse.urlencode(urllib.parse.unquote(raw_string))

        format_req = str.encode(f"v0:{timestamp}:{data}")
        encoded_secret = str.encode(config.SLACK_SECRET)
        request_hash = hmac.new(encoded_secret, format_req, hashlib.sha256).hexdigest()
        calculated_signature = f"v0={request_hash}"
        if hmac.compare_digest(calculated_signature, signature):
            return f(*args, **kwargs)

        return make_response(jsonify({'message': 'Invalid auth'})), 401
    return wrapper


def get_user_organisations(user):
    active_organisation = getattr(g, "active_organisation", None) or user.fallback_active_organisation()

    organisations = dict(
        active_organisation_id=active_organisation.id,
        organisations=organisations_schema.dump(user.organisations).data
    )

    return organisations


def get_denominations(currency_symbol=None):
    return DENOMINATION_DICT.get(currency_symbol, {})


def create_user_response_object(user, auth_token, message):
    try:
        if current_app.config['CHAINS'][user.default_organisation.token.chain]['IS_USING_BITCOIN']:
            usd_to_satoshi_rate = get_usd_to_satoshi_rate()
        else:
            usd_to_satoshi_rate = None
    except Exception:
        usd_to_satoshi_rate = None

    conversion_rate = 1
    currency_symbol = user.default_organisation.token.symbol if user.default_organisation and user.default_organisation.token else None
    display_decimals = user.default_organisation.token.display_decimals if user.default_organisation and user.default_organisation.token else None
    if user.default_currency:
        conversion = CurrencyConversion.query.filter_by(code=user.default_currency).first()
        if conversion is not None:
            conversion_rate = conversion.rate

    transfer_usages = []
    usage_objects = TransferUsage.query.filter_by(default=True).order_by(TransferUsage.priority).all()
    for usage in usage_objects:
        if ((usage.is_cashout and user.cashout_authorised) or not usage.is_cashout):
            transfer_usages.append({
                'id': usage.id,
                'name': usage.name,
                'icon': usage.icon,
                'priority': usage.priority,
                'translations': usage.translations
            })

    response_object = {
        'status': 'success',
        'message': message,
        'auth_token': auth_token.decode(),
        'user_id': user.id,
        'email': user.email,
        'admin_tier': user.admin_tier,
        'is_vendor': user.is_vendor,
        'is_supervendor': user.is_supervendor,
        'server_time': int(time.time() * 1000),
        'ecdsa_public': current_app.config['ECDSA_PUBLIC'],
        'pusher_key': current_app.config['PUSHER_KEY'],
        'display_decimals': display_decimals,
        'currency_symbol': currency_symbol,
        'currency_conversion_rate': conversion_rate,
        'secret': user.secret,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'deployment_name': current_app.config['DEPLOYMENT_NAME'],
        'denominations': get_denominations(currency_symbol=currency_symbol),
        'terms_accepted': user.terms_accepted,
        'request_feedback_questions': request_feedback_questions(user),
        'default_feedback_questions': current_app.config['DEFAULT_FEEDBACK_QUESTIONS'],
        'transfer_usages': transfer_usages,
        'forgiving_deduct': current_app.config['FORGIVING_DEDUCT'],
        'support_sig_validation': current_app.config['SUPPORT_SIG_VALIDATION'],
        'usd_to_satoshi_rate': usd_to_satoshi_rate,
        'kyc_active': True,  # todo; kyc active function
        'android_intercom_hash': create_intercom_secret(user_id=user.id, device_type='ANDROID'),
        'web_intercom_hash': create_intercom_secret(user_id=user.id, device_type='WEB'),
        'web_api_version': '1'
    }

    # merge the user and organisation object nicely (handles non-orgs well)
    response_object = {**response_object, **get_user_organisations(user)}

    # todo: fix this (now many to many)
    user_transfer_accounts = TransferAccount.query.execution_options(show_all=True).filter(
        TransferAccount.users.any(User.id.in_([user.id]))).all()
    if len(user_transfer_accounts) > 0:
        response_object['transfer_account_Id'] = [ta.id for ta in user_transfer_accounts]  # should change to plural
        response_object['name'] = user_transfer_accounts[0].name  # get the first transfer account name

    # if user.transfer_account:
    #     response_object['transfer_account_Id'] = user.transfer_account.id
    #     response_object['name'] = user.transfer_account.name

    return response_object