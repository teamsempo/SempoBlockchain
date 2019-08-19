from functools import wraps, partial
from flask import request, g, make_response, jsonify, current_app
from server import models, db

def requires_auth(f = None, required_roles=(), allowed_roles=(), ignore_tfa_requirement = False):
    if f is None:
        return partial(requires_auth, required_roles=required_roles, allowed_roles=allowed_roles, ignore_tfa_requirement = ignore_tfa_requirement)

    @wraps(f)
    def wrapper(*args, **kwargs):

        auth = request.authorization
        if auth and auth.type == 'basic':

            if (
                (len(allowed_roles) > 0 and 'basic_auth' not in allowed_roles)
                or (len(required_roles) > 0 and 'basic_auth' not in required_roles)
            ):
                responseObject = {
                    'status': 'fail',
                    'message': 'basic auth not allowed'
                }
                return make_response(jsonify(responseObject)), 401

            password = current_app.config['BASIC_AUTH_CREDENTIALS'].get(auth.username)
            if password and password == auth.password:
                return f(*args, **kwargs)
            else:
                responseObject = {
                    'status': 'fail',
                    'message': 'user not found'
                }
                return make_response(jsonify(responseObject)), 401

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

                    user = models.User.query.filter_by(id=resp['user_id']).first()

                    if not user:
                        responseObject = {
                            'status': 'fail',
                            'message': 'user not found'
                        }
                        return make_response(jsonify(responseObject)), 401


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

                    for required_role in required_roles:

                        if resp.get(required_role) != True:
                            responseObject = {
                                'status': 'fail',
                                'message': 'user does required role: ' + required_role,
                            }
                            return make_response(jsonify(responseObject)), 401

                    if len(allowed_roles) > 0:
                        has_an_allowed_role = False

                        for allowed_role in allowed_roles:

                            if resp.get(allowed_role) == True:
                                has_an_allowed_role = True

                        if has_an_allowed_role == False:
                            responseObject = {
                                'status': 'fail',
                                'message': 'user does not have any of the allowed roles: ' + str(allowed_roles),
                            }
                            return make_response(jsonify(responseObject)), 401

                    g.user = user

                    proxies = request.headers.getlist("X-Forwarded-For")
                    check_ip(proxies, user, num_proxy=1)

                    # updates the validated user last seen timestamp
                    user.update_last_seen_ts()
                    db.session.commit()

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
                'status': 'fail',
                'tfa_url': tfa_url,
                'message': 'User must setup two factor authentication'
            }

            return responseObject

        # Otherwise, check TFA
        tfa_response = models.User.decode_auth_token(tfa_token)
        if isinstance(tfa_response, str):
            # User doesn't have valid TFA token
            responseObject = {
                'status': 'fail',
                'tfa_failure': True,
                'message': tfa_response
            }
            return responseObject

        if tfa_response.get("user_id") != user.id:
            # User doesn't has valid TFA token BUT it's not theirs
            responseObject = {
                'status': 'fail',
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
