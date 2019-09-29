from functools import wraps, partial
from flask import request, g, make_response, jsonify, current_app
from server import db, models
import config, hmac, hashlib, json, urllib

from server.constants import ACCESS_ROLES

from server.exceptions import (
    TierNotFoundException,
    RoleNotFoundException
)

class AccessControl(object):

    @staticmethod
    def has_suffient_role(held_roles: dict, allowed_roles: dict) -> bool:
        for role in allowed_roles:
            try:
                required_tier = allowed_roles[role]
            except TypeError:
                raise Exception(
                    'Allowed roles must be a dictionary with roles as keys and required tier ranks as values, not {}'
                        .format(allowed_roles)
                )

            if AccessControl.has_sufficient_tier(held_roles, role, required_tier):
                return True

        return False

    @staticmethod
    def _get_tier_from_role_list(role_list, role):
        for role_obj in role_list:
            if role_obj.name == role and not role_obj.revoked:
                return role_obj.tier


    @staticmethod
    def has_exact_role(held_roles: dict, required_role: str, required_tier: str) -> bool:
        if required_role not in ACCESS_ROLES:
            raise RoleNotFoundException("Role '{}' not valid".format(required_role))
        if required_tier not in ACCESS_ROLES[required_role]:
            raise TierNotFoundException("Required tier {} not recognised".format(required_tier))

        if isinstance(held_roles,dict):
            return held_roles.get(required_role) == required_tier
        else:
            return AccessControl._get_tier_from_role_list(held_roles, required_role) == required_tier

    @staticmethod
    def has_sufficient_tier(held_roles: dict, required_role: str, required_tier: str) -> bool:

        if required_role not in ACCESS_ROLES:
            raise RoleNotFoundException("Role '{}' not valid".format(required_role))

        if required_role in held_roles:
            held_tier = held_roles[required_role]
            ranked_tiers = ACCESS_ROLES[required_role]

            if required_tier == 'any':
                return True

            if required_tier not in ranked_tiers:
                raise TierNotFoundException("Required tier {} not recognised for role {}"
                                            .format(required_tier, required_role))

            has_sufficient = AccessControl._held_tier_meets_required_tier(
                held_tier,
                required_tier,
                ranked_tiers
            )

            if has_sufficient:
                return True

        return False

    @staticmethod
    def has_any_tier(held_roles: dict, role: str):
        return AccessControl.has_sufficient_tier(held_roles, role, 'any')

    @staticmethod
    def _held_tier_meets_required_tier(held_tier: str, required_tier: str, tier_list: list) -> bool:
        if held_tier is None:
            return False

        try:
            held_rank = tier_list.index(held_tier)
        except ValueError:
            raise TierNotFoundException("Held tier {} not recognised".format(held_tier))
        try:
            required_rank = tier_list.index(required_tier)
        except ValueError:
            raise TierNotFoundException("Required tier {} not recognised".format(required_tier))

        # SMALLER ranks are more senior
        return held_rank <= required_rank

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

def requires_auth(f = None,
                  allowed_roles: dict={},
                  allowed_basic_auth_types: tuple=(), #['external', 'internal']
                  ignore_tfa_requirement=False):
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
                responseObject = {
                    'message': 'invalid basic auth username or password'
                }
                return make_response(jsonify(responseObject)), 401

            if len(allowed_basic_auth_types) == 0:
                response_object = {
                    'message': 'basic auth not allowed'
                }
                return make_response(jsonify(response_object)), 401

            if type not in allowed_basic_auth_types:
                responseObject = {
                    'message': 'Basic Auth type is {}. Must be: {}'.format(type, allowed_basic_auth_types)
                }
                return make_response(jsonify(responseObject)), 401

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

            resp = models.User.decode_auth_token(auth_token)

            if not isinstance(resp, str):

                    user = models.User.query.filter_by(id=resp['id']).execution_options(show_all=True).first()

                    if not user:
                        responseObject = {
                            'status': 'fail',
                            'message': 'user not found'
                        }
                        return make_response(jsonify(responseObject)), 401

                    g.user = user
                    # g.member_organisations = [org.id for org in user.organisations]
                    try:
                        primary_admin_organisation = user.get_primary_admin_organisation()
                        if primary_admin_organisation is not None:
                            g.primary_organisation_id = primary_admin_organisation.id
                        else:
                            g.primary_organisation_id = None
                    except NotImplementedError:
                        g.primary_organisation_id = None

                    if not user.is_activated:
                        responseObject = {
                            'status': 'fail',
                            'message': 'user not activated'
                        }
                        return make_response(jsonify(responseObject)), 401


                    if user.is_disabled:
                        responseObject = {
                            'status': 'fail',
                            'message': 'user has been disabled'
                        }
                        return make_response(jsonify(responseObject)), 401

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

            responseObject = {
                'status': 'fail',
                'message': resp
            }
            return make_response(jsonify(responseObject)), 401
        else:
            responseObject = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return make_response(jsonify(responseObject)), 401

    return wrapper


def tfa_logic(user, tfa_token, ignore_tfa_requirement=False):

    if (user.is_TFA_required() or user.TFA_enabled) and not ignore_tfa_requirement:
        if not user.TFA_enabled:
            # Go down this path if user is yet to set up TFA
            tfa_url = user.tfa_url
            responseObject = {
                'tfa_url': tfa_url,
                'message': 'User must setup two factor authentication'
            }

            return responseObject

        # Otherwise, check TFA
        if tfa_token is None:
            responseObject = {
                'tfa_failure': True,
                'message': 'TFA token required, none supplied'
            }
            return responseObject

        tfa_response = models.User.decode_auth_token(tfa_token, 'TFA')
        if isinstance(tfa_response, str):
            # User doesn't have valid TFA token
            responseObject = {
                'tfa_failure': True,
                'message': tfa_response
            }
            return responseObject

        if tfa_response.get("id") != user.id:
            # User doesn't has valid TFA token BUT it's not theirs
            responseObject = {
                'message': 'Invalid User ID in TFA response'
            }

            return responseObject

    return None


def check_ip(proxies, user, num_proxy=0):
    """
    Proxies can be faked easily. Assumes there is a set number of proxies in production.
    Todo: make this more robust
    """
    correct_ip_index = num_proxy + 1

    if len(proxies) >= correct_ip_index:
        real_ip_address = proxies[-correct_ip_index]  # get the correct referring client ip
        if real_ip_address is not None and not models.IpAddress.check_user_ips(user, real_ip_address):
            # IP exists in request and is not already saved
            new_ip = models.IpAddress(ip=real_ip_address)
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
