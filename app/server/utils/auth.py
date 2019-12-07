from functools import wraps, partial
from flask import request, g, make_response, jsonify, current_app
from server import db
from server.models.user import User
from server.models.ip_address import IpAddress
from server.models.organisation import Organisation
from server.utils.access_control import AccessControl
import config, hmac, hashlib, json, urllib
from typing import Optional, List, Dict

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


def requires_auth(f=None,
                  allowed_roles: Optional[Dict]=None,
                  allowed_basic_auth_types: Optional[List]=None,  # currently 'external' or 'internal'
                  ignore_tfa_requirement: bool=False):

    allowed_roles = allowed_roles or {}
    allowed_basic_auth_types = allowed_basic_auth_types or []

    if f is None:
        return partial(requires_auth,
                       allowed_roles=allowed_roles,
                       allowed_basic_auth_types=allowed_basic_auth_types,
                       ignore_tfa_requirement = ignore_tfa_requirement)

    @wraps(f)
    def wrapper(*args, **kwargs):

        auth = request.authorization

        if auth and auth.type == 'basic':
            (password, type) = current_app.config['BASIC_AUTH_CREDENTIALS'].get(auth.username, (None, None))
            if password is None or password != auth.password:
                response_object = {
                    'message': 'invalid basic auth username or password'
                }
                return make_response(jsonify(response_object)), 401

            if len(allowed_basic_auth_types) == 0:
                response_object = {
                    'message': 'basic auth not allowed'
                }
                return make_response(jsonify(response_object)), 401

            if type not in allowed_basic_auth_types:
                response_object = {
                    'message': 'Basic Auth type is {}. Must be: {}'.format(type, allowed_basic_auth_types)
                }
                return make_response(jsonify(response_object)), 401

            return f(*args, **kwargs)

        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header != 'null':
            split_header = auth_header.split("|")
            auth_token = split_header[0]
            try:
                tfa_token = split_header[1]
            except IndexError:
                # Auth header does not contain a TFA token, try getting it from explicit header instead
                # (dev convenience)
                tfa_token = request.headers.get('TFA_Authorization', '')
        else:
            auth_token = ''
            tfa_token = ''

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

                    except NotImplementedError:
                        g.active_organisation = None

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
                            return make_response(jsonify(response_object)), 401


                    proxies = request.headers.getlist("X-Forwarded-For")
                    check_ip(proxies, user, num_proxy=1)

                    # updates the validated user last seen timestamp
                    user.update_last_seen_ts()
                    # db.session.commit() todo: fix this. can't commit here as means we lose context

                    #This is the point where you've made it through ok and you can return the top method
                    return f(*args, **kwargs)

            response_object = {
                'status': 'fail',
                'message': resp
            }
            return make_response(jsonify(response_object)), 401
        else:
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

        if tfa_response.get("id") != user.id:
            # User doesn't has valid TFA token BUT it's not theirs
            response_object = {
                'message': 'Invalid User ID in TFA response'
            }

            return response_object

    return None


def check_ip(proxies, user, num_proxy=0):
    """
    Proxies can be faked easily. Assumes there is a set number of proxies in production.
    Todo: make this more robust
    """
    correct_ip_index = num_proxy + 1

    if len(proxies) >= correct_ip_index:
        real_ip_address = proxies[-correct_ip_index]  # get the correct referring client ip
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
