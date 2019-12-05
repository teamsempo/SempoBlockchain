from flask import Blueprint, request, make_response, jsonify, g, current_app
from flask.views import MethodView
from server import db, sentry
# from server import limiter
from server.constants import DENOMINATION_DICT
from server.models.transfer_account import TransferAccount
from phonenumbers.phonenumberutil import NumberParseException
from server.models.user import User
from server.models.organisation import Organisation
from server.models.email_whitelist import EmailWhitelist
from server.models.currency_conversion import CurrencyConversion
from server.models.blacklist_token import BlacklistToken
from server.models.transfer_usage import TransferUsage
from server.utils.intercom import create_intercom_secret
from server.utils.auth import requires_auth, tfa_logic
from server.utils.access_control import AccessControl
from server.utils import user as UserUtils
from server.utils.phone import proccess_phone_number
from server.utils.feedback import request_feedback_questions
from server.utils.amazon_ses import send_reset_email, send_activation_email, send_invite_email
from server.utils.blockchain_transaction import get_usd_to_satoshi_rate

import time, random

auth_blueprint = Blueprint('auth', __name__)


def get_user_organisations(user):
    try:
        organisations = dict(
            active_organisation_name=g.active_organisation.name,
            active_organisation_id=g.active_organisation_id,
            organisations=[dict(id=org.id, name=org.name) for org in user.organisations]
        )
    except AttributeError:
        organisations = dict(
            active_organisation_name=user.default_organisation.name,
            active_organisation_id=user.default_organisation.id,
            organisations=[dict(id=org.id, name=org.name) for org in user.organisations]
        )

    return organisations


def get_denominations():
    currency_name = current_app.config['CURRENCY_NAME']
    return DENOMINATION_DICT.get(currency_name, {})


def create_user_response_object(user, auth_token, message):
    if current_app.config['IS_USING_BITCOIN']:
        try:
            usd_to_satoshi_rate = get_usd_to_satoshi_rate()
        except Exception:
            usd_to_satoshi_rate = None
    else:
        usd_to_satoshi_rate = None

    conversion_rate = 1
    currency_name = current_app.config['CURRENCY_NAME']
    if user.default_currency:
        conversion = CurrencyConversion.query.filter_by(code=user.default_currency).first()
        if conversion is not None:
            conversion_rate = conversion.rate
            currency_name = user.default_currency

    transfer_usages = []
    usage_objects = TransferUsage.query.order_by(TransferUsage.priority).limit(11).all()
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
        'currency_decimals': current_app.config['CURRENCY_DECIMALS'],
        'currency_name': currency_name,
        'currency_conversion_rate': conversion_rate,
        'secret': user.secret,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'deployment_name': current_app.config['DEPLOYMENT_NAME'],
        'denominations': get_denominations(),
        'terms_accepted': user.terms_accepted,
        'request_feedback_questions': request_feedback_questions(user),
        'default_feedback_questions': current_app.config['DEFAULT_FEEDBACK_QUESTIONS'],
        'transfer_usages': transfer_usages,
        'usd_to_satoshi_rate': usd_to_satoshi_rate,
        'kyc_active': True,  # todo; kyc active function
        'android_intercom_hash': create_intercom_secret(user_id=user.id, device_type='ANDROID'),
        'web_intercom_hash': create_intercom_secret(user_id=user.id, device_type='WEB'),
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


class CheckBasicAuth(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def get(self):
        response_object = {
            'status': 'success',
        }

        return make_response(jsonify(response_object)), 201


class RefreshTokenAPI(MethodView):
    """
    User Refresh Token Resource
    """

    @requires_auth
    def get(self):
        try:

            auth_token = g.user.encode_auth_token()

            response_object = create_user_response_object(g.user, auth_token, 'Token refreshed successfully.')

            return make_response(jsonify(response_object)), 201

        except Exception as e:

            response_object = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.'
            }

            return make_response(jsonify(response_object)), 403


class RegisterAPI(MethodView):
    """
    User Registration Resource
    """

    def post(self):
        # get the post data
        post_data = request.get_json()

        email = post_data.get('email') or post_data.get('username')
        password = post_data.get('password')
        phone = post_data.get('phone')
        referral_code = post_data.get('referral_code')

        if phone is not None:
            # this is a registration from a mobile device THUS a vendor or recipient.
            response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
                post_data,
                is_self_sign_up=True,
            )

            if response_code == 200:
                db.session.commit()

            return make_response(jsonify(response_object)), response_code

        # email_tail = email.split('@')[-1]
        email_ok = False

        whitelisted_emails = EmailWhitelist.query\
            .filter_by(email=email, referral_code=referral_code, used=False) \
            .execution_options(show_all=True).all()

        selected_whitelist_item = None
        exact_match = False

        tier = None
        if '@sempo.ai' in email or '@withsempo.com' in email:
            email_ok = True
            tier = 'sempoadmin'

        for whitelisted in whitelisted_emails:
            if whitelisted.allow_partial_match and whitelisted.email in email:
                email_ok = True
                tier = whitelisted.tier
                selected_whitelist_item = whitelisted
                exact_match = False
                continue
            elif whitelisted.email == email:
                email_ok = True

                whitelisted.used = True
                tier = whitelisted.tier
                selected_whitelist_item = whitelisted
                exact_match = True
                continue

        if not email_ok:
            response_object = {
                'status': 'fail',
                'message': 'Invalid email domain.',
            }
            return make_response(jsonify(response_object)), 403

        if len(password) < 7:
            response_object = {
                'status': 'fail',
                'message': 'Password must be at least 6 characters long',
            }
            return make_response(jsonify(response_object)), 403

        # check if user already exists
        user = User.query.filter_by(email=email).execution_options(show_all=True).first()
        if user:
            response_object = {
                'status': 'fail',
                'message': 'User already exists. Please Log in.',
            }
            return make_response(jsonify(response_object)), 403

        if tier is None:
            tier = 'subadmin'

        user = User()

        if selected_whitelist_item:
            organisation = selected_whitelist_item.organisation
        else:
            organisation = None

        user.create_admin_auth(email, password, tier, organisation)

        # insert the user
        db.session.add(user)


        db.session.flush()

        if exact_match:
            user.is_activated = True

            auth_token = user.encode_auth_token()

            response_object = {
                'status': 'success',
                'message': 'Successfully activated.',
                'auth_token': auth_token.decode(),
                'user_id': user.id,
                'email': user.email,
            }

            db.session.commit()

            return make_response(jsonify(response_object)), 201

        activation_token = user.encode_single_use_JWS('A')

        send_activation_email(activation_token, email)

        db.session.commit()

        # generate the auth token
        response_object = {
            'status': 'success',
            'message': 'Successfully registered.',
        }

        return make_response(jsonify(response_object)), 201


class ActivateUserAPI(MethodView):
    """
    User Registration Resource
    """

    def post(self):
        # get the post data
        post_data = request.get_json()

        activation_token = post_data.get('activation_token')

        if activation_token and activation_token != 'null':
            auth_token = activation_token.split(" ")[0]
        else:
            auth_token = ''
        if auth_token:

            validity_check = User.decode_single_use_JWS(activation_token, 'A')

            if not validity_check['success']:
                response_object = {
                    'status': 'fail',
                    'message': validity_check['message']
                }

                return make_response(jsonify(response_object)), 401

            user = validity_check['user']

            if user.is_activated:
                response_object = {
                    'status': 'fail',
                    'message': 'Already activated.'
                }

                return make_response(jsonify(response_object)), 401

            user.is_activated = True

            auth_token = user.encode_auth_token()

            response_object = {
                'status': 'success',
                'message': 'Successfully activated.',
                'auth_token': auth_token.decode(),
                'user_id': user.id,
                'email': user.email,
            }

            db.session.commit()

            return make_response(jsonify(response_object)), 201

        else:
            response_object = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return make_response(jsonify(response_object)), 401


class LoginAPI(MethodView):
    """
    User Login Resource
    """

    def get(self):

        print("process started")

        challenges = [
            ('Why don’t they play poker in the jungle?', 'Too many cheetahs.'),
            ('What did the Buddhist say to the hot dog vendor?', 'Make me one with everything.'),
            ('What does a zombie vegetarian eat?', 'Graaaaaaaains!'),
            ('My new thesaurus is terrible.', 'Not only that, but it’s also terrible.'),
            ('Why didn’t the astronaut come home to his wife?', 'He needed his space.'),
            ('I got fired from my job at the bank today.',
             'An old lady came in and asked me to check her balance, so I pushed her over.'),
            ('I like to spend every day as if it’s my last',
             'Staying in bed and calling for a nurse to bring me more pudding.')
        ]

        challenge = random.choice(challenges)

        # time.sleep(int(request.args.get('delay', 0)))
        # from functools import reduce
        # reduce(lambda x, y: x + y, range(0, int(request.args.get('count', 1))))

        # memory_to_consume = int(request.args.get('MB', 0)) * 1000000
        # bytearray(memory_to_consume)

        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.environ["HTTP_USER_AGENT"]
        ip = request.environ["REMOTE_ADDR"]
        # proxies = request.headers.getlist("X-Forwarded-For")
        # http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html

        response_object = {
            'status': 'success',
            'who_allows_a_get_request_to_their_auth_endpoint': 'We do.',
            challenge[0]: challenge[1],
            # 'metadata': {'user_agent': user_agent, 'ip': ip_address, 'otherip': ip, 'proxies': proxies},
        }
        return make_response(jsonify(response_object)), 200

    # @limiter.limit("20 per day")
    def post(self):
        # get the post data

        post_data = request.get_json()

        user = None
        phone = None

        email = post_data.get('username') or post_data.get('email')
        password = post_data.get('password')
        tfa_token = post_data.get('tfa_token')

        # First try to match email
        if email:
            user = User.query.filter_by(email=email).execution_options(show_all=True).first()

        # Now try to match the public serial number (comes in under the phone)
        if not user:
            public_serial_number_or_phone = post_data.get('phone')

            user = User.query.filter_by(public_serial_number=public_serial_number_or_phone).execution_options(
                show_all=True).first()

        # Now try to match the phone
        if not user:
            try:
                phone = proccess_phone_number(post_data.get('phone'), region=post_data.get('region'))
            except NumberParseException as e:
                response_object = {'message': 'Invalid Phone Number: ' + str(e)}
                return make_response(jsonify(response_object)), 401

            if phone:
                user = User.query.filter_by(phone=phone).execution_options(show_all=True).first()

        # mobile user doesn't exist so default to creating a new wallet!
        if user is None and phone:
            # this is a registration from a mobile device THUS a vendor or recipient.
            response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
                dict(phone=phone, deviceInfo=post_data.get('deviceInfo')),
                is_self_sign_up=True,
            )

            if response_code == 200:
                db.session.commit()

            return make_response(jsonify(response_object)), response_code

        if user and user.is_activated and post_data.get('phone') and (password == ''):
            # user already exists, is activated. no password provided, thus request PIN screen.
            # todo: this should check if device exists, if no, resend OTP to verify login is real.
            response_object = {
                'status': 'success',
                'login_with_pin': True,
                'message': 'Login with PIN'
            }
            return make_response(jsonify(response_object)), 200

        if not (email or post_data.get('phone')):
            response_object = {
                'status': 'fail',
                'message': 'No username supplied'
            }
            return make_response(jsonify(response_object)), 401

        if post_data.get('phone') and user and user.one_time_code and not user.is_activated:
            # vendor sign up with one time code or OTP verified
            if user.one_time_code == password:
                response_object = {
                    'status': 'success',
                    'pin_must_be_set': True,
                    'message': 'Please set your pin.'
                }
                return make_response(jsonify(response_object)), 200

            if not user.is_phone_verified:
                if user.is_self_sign_up:
                    # self sign up, resend phone verification code
                    user.set_pin(None, False)  # resets PIN
                    UserUtils.send_one_time_code(phone=phone, user=user)
                db.session.commit()
                response_object = {'message':  'Please verify phone number.', 'otp_verify': True}
                return make_response(jsonify(response_object)), 200

        try:

            if not user or not user.verify_password(password):
                response_object = {
                    'status': 'fail',
                    'message': 'Invalid username or password'
                }

                return make_response(jsonify(response_object)), 401

            if not user.is_activated:
                response_object = {
                    'status': 'fail',
                    'is_activated': False,
                    'message': 'Account has not been activated. Please check your emails.'
                }
                return make_response(jsonify(response_object)), 401

            if post_data.get('deviceInfo'):
                UserUtils.save_device_info(post_data.get('deviceInfo'), user)

            auth_token = user.encode_auth_token()

            if not auth_token:
                response_object = {
                    'status': 'fail',
                    'message': 'Invalid username or password'
                }
                return make_response(jsonify(response_object)), 401

            # Possible Outcomes:
            # TFA required, but not set up
            # TFA enabled, and user does not have valid TFA token
            # TFA enabled, and user has valid TFA token
            # TFA not required

            tfa_response_oject = tfa_logic(user, tfa_token)
            if tfa_response_oject:
                tfa_response_oject['auth_token'] = auth_token.decode()

                return make_response(jsonify(tfa_response_oject)), 401

            # Update the last_seen TS for this user
            user.update_last_seen_ts()

            response_object = create_user_response_object(user, auth_token, 'Successfully logged in.')

            db.session.commit()

            return make_response(jsonify(response_object)), 200

        except Exception as e:

            sentry.captureException()

            raise e

            # response_object = {
            #     'status': 'fail',
            #     'message': "Unknown Error."
            # }
            #
            # return make_response(jsonify(response_object)), 500


class LogoutAPI(MethodView):
    """
    Logout Resource
    """

    def post(self):
        # get auth token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[0]
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                # mark the token as blacklisted
                blacklist_token = BlacklistToken(token=auth_token)
                try:
                    # insert the token
                    db.session.add(blacklist_token)
                    db.session.commit()
                    response_object = {
                        'status': 'success',
                        'message': 'Successfully logged out.'
                    }
                    return make_response(jsonify(response_object)), 200
                except Exception as e:
                    response_object = {
                        'status': 'fail',
                        'message': e
                    }
                    return make_response(jsonify(response_object)), 200
            else:
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
            return make_response(jsonify(response_object)), 403


class RequestPasswordResetEmailAPI(MethodView):
    """
    Password Reset Email Resource
    """

    def post(self):
        # get the post data
        post_data = request.get_json()

        email = post_data.get('email')

        if not email:
            response_object = {
                'status': 'fail',
                'message': 'No email supplied'
            }

            return make_response(jsonify(response_object)), 401

        user = User.query.filter_by(email=email).execution_options(show_all=True).first()

        if user:
            password_reset_token = user.encode_single_use_JWS('R')
            user.save_password_reset_token(password_reset_token)
            send_reset_email(password_reset_token, email)

        response_object = {
            'status': 'success',
            'message': 'Reset email sent'
        }

        return make_response(jsonify(response_object)), 200


class ResetPasswordAPI(MethodView):
    """
    Password Reset Resource
    """

    def post(self):

        # get the post data
        post_data = request.get_json()

        old_password = post_data.get('old_password')
        new_password = post_data.get('new_password')
        phone = proccess_phone_number(phone_number=post_data.get('phone'), region=post_data.get('region'))
        one_time_code = post_data.get('one_time_code')

        auth_header = request.headers.get('Authorization')

        # Check authorisation using a one time code
        if phone and one_time_code:
            card = phone[-6:]
            user = (User.query.filter_by(phone=phone).execution_options(show_all=True).first() or
                    User.query.filter_by(public_serial_number=card).execution_options(show_all=True).first()
                    )

            if not user:
                response_object = {
                    'status': 'fail',
                    'message': 'User not found'
                }

                return make_response(jsonify(response_object)), 401

            if user.is_activated:
                response_object = {
                    'status': 'fail',
                    'message': 'Account already activated'
                }

                return make_response(jsonify(response_object)), 401

            if str(one_time_code) != user.one_time_code:
                response_object = {
                    'status': 'fail',
                    'message': 'One time code not valid'
                }

                return make_response(jsonify(response_object)), 401

            user.hash_password(new_password)

            user.is_phone_verified = True
            user.is_activated = True
            user.one_time_code = None

            auth_token = user.encode_auth_token()

            response_object = create_user_response_object(user, auth_token, 'Successfully set pin')

            db.session.commit()

            return make_response(jsonify(response_object)), 200

        # Check authorisation using regular auth
        elif auth_header and auth_header != 'null' and old_password:
            auth_token = auth_header.split(" ")[0]

            resp = User.decode_auth_token(auth_token)

            if isinstance(resp, str):
                response_object = {
                    'status': 'fail',
                    'message': 'Invalid auth token'
                }

                return make_response(jsonify(response_object)), 401

            user = User.query.filter_by(id=resp.get('user_id')).execution_options(show_all=True).first()

            if not user:
                response_object = {
                    'status': 'fail',
                    'message': 'User not found'
                }

                return make_response(jsonify(response_object)), 401

            if not user.verify_password(old_password):
                response_object = {
                    'status': 'fail',
                    'message': 'invalid password'
                }

                return make_response(jsonify(response_object)), 401

        # Check authorisation using a reset token provided via email
        else:

            reset_password_token = post_data.get('reset_password_token')

            if not reset_password_token:
                response_object = {
                    'status': 'fail',
                    'message': 'Missing token.'
                }

                return make_response(jsonify(response_object)), 401

            reset_password_token = reset_password_token.split(" ")[0]

            validity_check = User.decode_single_use_JWS(reset_password_token, 'R')

            if not validity_check['success']:
                response_object = {
                    'status': 'fail',
                    'message': validity_check['message']
                }

                return make_response(jsonify(response_object)), 401

            user = validity_check['user']

            reuse_check = user.check_reset_token_already_used(
                reset_password_token)

            
            if not reuse_check:
                response_object = {
                    'status': 'fail',
                    'message': 'Token already used'
                }

                return make_response(jsonify(response_object)), 401

        if not new_password or len(new_password) < 6:
            response_object = {
                'status': 'fail',
                'message': 'Password must be at least 6 characters long'
            }

            return make_response(jsonify(response_object)), 401

        user.hash_password(new_password)
        user.delete_password_reset_tokens()
        db.session.commit()

        response_object = {
            'status': 'success',
            'message': 'Password changed, please log in'
        }

        return make_response(jsonify(response_object)), 200


class PermissionsAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):

        admins = User.query.filter_by(has_admin_role=True).all()

        admin_list = []
        for admin in admins:

            tier = admin.admin_tier

            admin_list.append({
                'id': admin.id,
                'email': admin.email,
                'admin_tier': tier,
                'created': admin.created,
                'is_activated': admin.is_activated,
                'is_disabled': admin.is_disabled
            })

        response_object = {
            'status': 'success',
            'message': 'Admin List Loaded',
            'admin_list': admin_list
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):

        post_data = request.get_json()

        email = post_data.get('email')
        tier = post_data.get('tier')
        organisation_id = post_data.get('organisation_id', None)

        if organisation_id and not AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'sempoadmin'):
            response_object = {'message': 'Not Authorised to set organisation ID'}
            return make_response(jsonify(response_object)), 401

        target_organisation_id = organisation_id or g.active_organisation
        if not target_organisation_id:
            response_object = {'message': 'Must provide an organisation to bind user to'}
            return make_response(jsonify(response_object)), 400

        organisation = Organisation.query.get(target_organisation_id)
        if not organisation:
            response_object = {'message': 'Organisation Not Found'}
            return make_response(jsonify(response_object)), 404

        email_exists = EmailWhitelist.query.filter_by(email=email).first()

        if email_exists:
            response_object = {'message': 'Email already on whitelist.'}
            return make_response(jsonify(response_object)), 400

        if not (email and tier):
            response_object = {'message': 'No email or tier provided'}
            return make_response(jsonify(response_object)), 400

        invite = EmailWhitelist(email=email,
                                tier=tier,
                                organisation_id=target_organisation_id)

        db.session.add(invite)

        send_invite_email(invite, organisation)

        db.session.commit()

        all_invites = EmailWhitelist.query.all()

        print(all_invites)

        response_object = {
            'message': 'An invite has been sent!',
            'referral_code': invite.referral_code
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def put(self):

        post_data = request.get_json()

        user_id = post_data.get('user_id')
        admin_tier = post_data.get('admin_tier')
        deactivated = post_data.get('deactivated', None)

        user = User.query.get(user_id)

        if not user:
            response_object = {
                'status': 'fail',
                'message': 'User not found'
            }

            return make_response(jsonify(response_object)), 401

        if admin_tier:
            user.set_held_role('ADMIN',admin_tier)

        if deactivated is not None:
            user.is_disabled = deactivated

        db.session.commit()

        response_object = {
            'status': 'success',
            'message': 'Account status modified',
        }

        return make_response(jsonify(response_object)), 200


class BlockchainKeyAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def get(self):
        response_object = {
            'status': 'success',
            'message': 'Key loaded',
            'private_key': current_app.config['MASTER_WALLET_PRIVATE_KEY'],
            'address': current_app.config['MASTER_WALLET_ADDRESS']
        }

        return make_response(jsonify(response_object)), 200


class KoboCredentialsAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):
        response_object = {
            'username': current_app.config['EXTERNAL_AUTH_USERNAME'],
            'password': current_app.config['EXTERNAL_AUTH_PASSWORD']
        }

        return make_response(jsonify(response_object)), 200


class TwoFactorAuthAPI(MethodView):
    @requires_auth
    def get(self):
        tfa_url = g.user.tfa_url
        response_object = {
            'data': {"tfa_url": tfa_url}
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(ignore_tfa_requirement=True)
    def post(self):
        request_data = request.get_json()
        user = g.user
        otp_token = request_data.get('otp')
        otp_expiry_interval = request_data.get('otp_expiry_interval')

        malformed_otp = False
        try:
            int(otp_token)
        except ValueError:
            malformed_otp = True

        if not isinstance(otp_token, str) or len(otp_token) != 6:
            malformed_otp = True

        if malformed_otp:
            response_object = {
                'status': "Failed",
                'message': "OTP must be a 6 digit numeric string"
            }

            return make_response(jsonify(response_object)), 400

        if user.validate_OTP(otp_token):
            tfa_auth_token = user.encode_TFA_token(otp_expiry_interval)
            user.TFA_enabled = True

            db.session.commit()

            if tfa_auth_token:
                auth_token = g.user.encode_auth_token()

                response_object = create_user_response_object(user, auth_token, 'Successfully logged in.')

                response_object['tfa_auth_token'] = tfa_auth_token.decode()

                return make_response(jsonify(response_object)), 200

        response_object = {
            'status': "Failed",
            'message': "Validation failed. Please try again."
        }

        return make_response(jsonify(response_object)), 400


# add Rules for API Endpoints

auth_blueprint.add_url_rule(
    '/auth/check_basic_auth/',
    view_func=CheckBasicAuth.as_view('check_basic_auth'),
    methods=['GET']
)

auth_blueprint.add_url_rule(
    '/auth/refresh_api_token/',
    view_func=RefreshTokenAPI.as_view('refresh_token_api'),
    methods=['GET']
)

auth_blueprint.add_url_rule(
    '/auth/register/',
    view_func=RegisterAPI.as_view('register_api'),
    methods=['POST']
)

auth_blueprint.add_url_rule(
    '/auth/request_api_token/',
    view_func=LoginAPI.as_view('login_api'),
    methods=['POST', 'GET']
)

auth_blueprint.add_url_rule(
    '/auth/logout/',
    view_func=LogoutAPI.as_view('logout_view'),
    methods=['POST']
)

auth_blueprint.add_url_rule(
    '/auth/activate/',
    view_func=ActivateUserAPI.as_view('activate_view'),
    methods=['POST']
)

auth_blueprint.add_url_rule(
    '/auth/reset_password/',
    view_func=ResetPasswordAPI.as_view('reset_view'),
    methods=['POST']
)

auth_blueprint.add_url_rule(
    '/auth/request_reset_email/',
    view_func=RequestPasswordResetEmailAPI.as_view('request_reset_email_view'),
    methods=['POST']
)

auth_blueprint.add_url_rule(
    '/auth/permissions/',
    view_func=PermissionsAPI.as_view('permissions_view'),
    methods=['POST', 'PUT', 'GET']
)

auth_blueprint.add_url_rule(
    '/auth/blockchain/',
    view_func=BlockchainKeyAPI.as_view('blockchain_view'),
    methods=['GET']
)

auth_blueprint.add_url_rule(
    '/auth/kobo/',
    view_func=KoboCredentialsAPI.as_view('kobo_view'),
    methods=['GET']
)

auth_blueprint.add_url_rule(
    '/auth/tfa/',
    view_func=TwoFactorAuthAPI.as_view('tfa_view'),
    methods=['GET', 'POST']
)
