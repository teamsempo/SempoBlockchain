from flask import make_response
from server import db
from server.models import KycApplication, User
from server.utils.phone import send_generic_message
from server.utils.namescan import run_namescam_aml_check

import config, slack, json

# Slack client for Web API requests
client = slack.WebClient(token=config.SLACK_API_TOKEN)

# help-verify channel
CHANNEL_ID = 'CN1NE0G8P'


def generate_deny_button(user_id):
    return {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "Deny"
            },
        "style": "danger",
        "value": "deny-{}".format(user_id)
        }


def generate_approve_button(user_id):
    return {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "Approve"
            },
        "style": "primary",
        "value": "approve-{}".format(user_id)
        }


def generate_start_button(user_id):
    return {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "Start"
            },
        "style": "primary",
        "value": "start-{}".format(user_id)
        }


def generate_actions(*args):
    return {"type": "actions", "elements": [arg for arg in args]}


def generate_blocks(phone=None,first_name=None,last_name=None,dob=None,address=None,document_type=None, document_front_url=None, document_back_url=None, selfie_url=None):
    return [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "You have a new verification request:\n*{}*".format(phone)
        }},
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [{
                "type": "mrkdwn",
                "text": "*First Name:*\n{}".format(first_name)
            }, {
                "type": "mrkdwn",
                "text": "*Last Name::*\n{}".format(last_name)
            }, {
                "type": "mrkdwn",
                "text": "*DOB:*\n{}".format(dob)
            }, {
                "type": "mrkdwn",
                "text": "*Address:*\n{}".format(address)
            }, {
                "type": "mrkdwn",
                "text": "*{} (front):*\n<{}|View>".format(document_type,document_front_url)
            }, {
                "type": "mrkdwn",
                "text": "*{} (back):*\n<{}|View>".format(document_type,document_back_url)
            }, {
                "type": "mrkdwn",
                "text": "*Selfie:*\n<{}|View>".format(selfie_url)
            }]
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Start verification process. <https://sempo.slack.com/archives/CN1NE0G8P/p1567854805002100|Help.>"
                }
            ]
        },
    ]


def filter_for_url(key=None, array=None):
    files = sorted(list(filter(lambda x: x.user_filename == key, array)), key=lambda doc: doc.created)
    if len(files) >= 1:
        return files[0].file_url  # returns the newest document of the correct key
    return None


def generate_populated_message(user_id=None):
    kyc_details=None
    if user_id:
        kyc_details = KycApplication.query.execution_options(show_all=True).filter_by(user_id=user_id).first()

    documents = kyc_details.uploaded_documents
    return generate_blocks(
        phone=kyc_details.phone,
        first_name=kyc_details.first_name,
        last_name=kyc_details.last_name,
        dob=kyc_details.dob,
        address=kyc_details.street_address,
        document_type=documents[0].reference,
        document_front_url=filter_for_url('document_front_base64', documents),
        document_back_url=filter_for_url('document_back_base64', documents),
        selfie_url=filter_for_url('selfie_base64', documents),
    )


def post_verification_message(user=None):
    # Post verification message to slack channel

    message_blocks = generate_populated_message(user_id=user.id)
    action_block = generate_actions(generate_start_button(user_id=user.id))
    message_blocks.append(action_block)

    result = client.chat_postMessage(
        channel=CHANNEL_ID,
        text=':white_check_mark: New Verify Task',
        blocks=message_blocks
    )
    return result


def get_user_from_id(user_id, payload):
    user = User.query.execution_options(show_all=True).filter_by(id=user_id).first()

    if user is None or len(user.kyc_applications) < 0:
        client.chat_update(
            channel=CHANNEL_ID,
            ts=payload["state"],
            text="Oh damn, we've had a bad error on our server. @nick and @tristan to fix."
        )
        return make_response("", 200)
    return user


def approve_user(message_blocks, username, message_ts, phone):
    new_message_blocks = message_blocks[:len(message_blocks) - 1]
    new_message_blocks.append(dict(type='context', elements=[
        {"type": 'mrkdwn',
         "text": ':white_check_mark: *@{}* Completed a verification!'.format(username)}]))

    client.chat_update(
        channel=CHANNEL_ID,
        ts=message_ts,
        blocks=new_message_blocks
    )

    if phone:
        send_generic_message(to_phone=phone,
                             message='Hooray! Your identity has been successfully verified and Sempo account limits lifted.')

    return make_response("", 200)


def generate_aml_message(parent_message_ts=None, aml_result=None, avg_match_rate=0):
    message_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":female-detective: *New AML report*"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Date:*\n{}".format(aml_result.get('date'))
                },
                {
                    "type": "mrkdwn",
                    "text": "*Scan ID:*\n{}".format(aml_result.get('scan_id'))
                },
                {
                    "type": "mrkdwn",
                    "text": "*Number of Matches:*\n{}".format(aml_result.get('number_of_matches'))
                },
                {
                    "type": "mrkdwn",
                    "text": "*Avg Match Rate:*\n{}".format(avg_match_rate)
                }
            ]
        },
        {
            "type": "divider"
        }
    ]

    persons = aml_result.get('persons', None)
    if persons is not None:
        for index, person in enumerate(persons, 1):
            markdown = ""
            markdown = markdown + "Match {} \n\n".format(index)
            for (key, value) in person.items():
                if isinstance(value, list):
                    value = " ".join(str(x) for x in value)
                markdown = markdown + '• {} -- {} \n'.format(key, value)

            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": markdown
                }
            })

    client.chat_postMessage(
        channel=CHANNEL_ID,
        thread_ts=parent_message_ts,
        blocks=message_blocks
    )


def slack_controller(payload):
    # Parse the request payload

    if payload["type"] == "block_actions":
        # the user has interacted with the message

        if "start" in payload['actions'][0]['value']:
            # Show the user details dialog to the user
            user_id = payload['actions'][0]['value'].split('-')[1]
            client.dialog_open(
                trigger_id=payload["trigger_id"],
                dialog={
                    "title": "Verify User",
                    "submit_label": "Next",
                    "callback_id": "user_details_form-" + user_id,
                    "state": payload['message']['ts'],
                    "elements": [
                        {
                            "label": "ID Validity",
                            "type": "select",
                            "name": "id_validity",
                            "options": [
                                {
                                    "label": ":white_check_mark: ID is valid, non-expired and photo matches selfie",
                                    "value": "valid"
                                },
                                {
                                    "label": ":x: ID is not valid or expired",
                                    "value": "non_valid"
                                },
                                {
                                    "label": ":x: ID document or selfie is too blurry",
                                    "value": "id_blurry"
                                },
                                {
                                    "label": ":x: ID photo does not match selfie",
                                    "value": "no_match_selfie"
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "label": "First Name",
                            "name": "first_name",
                            "optional": True
                        },
                        {
                            "type": "text",
                            "label": "Last Name",
                            "name": "last_name",
                            "optional": True
                        },
                        {
                            "type": "text",
                            "label": "Date of Birth (DD/MM/YYYY) or (YYYY)",
                            "name": "date_of_birth",
                            "optional": True
                        },
                        {
                            "type": "text",
                            "label": "Residential Address",
                            "name": "address",
                            "optional": True
                        }
                    ]
                }
            )

            # Update the message to show that we're in the process of verifying a user
            message_blocks = payload['message']['blocks']
            new_message_blocks = message_blocks[:len(message_blocks) - 2]
            new_message_blocks.append(dict(type='context', elements=[{"type": 'mrkdwn', "text": ':pencil: *@{}* started verifying...'.format(payload['user']['username'])}]))
            action_blocks = generate_actions(generate_start_button(user_id=user_id))
            new_message_blocks.append(action_blocks)

            client.chat_update(
                channel=CHANNEL_ID,
                ts=payload["message"]["ts"],
                blocks=new_message_blocks
            )

        elif "approve" in payload['actions'][0]['value']:
            user_id = payload['actions'][0]['value'].split('-')[1]
            user = get_user_from_id(user_id, payload)
            user.kyc_applications[0].kyc_status = 'VERIFIED'

            # Update the message to show we've verified a user
            message_blocks = payload['message']['blocks']
            return approve_user(message_blocks, username=payload['user']['username'], message_ts=payload["message"]["ts"], phone=user.phone)

        elif "deny" in payload['actions'][0]['value']:
            user_id = payload['actions'][0]['value'].split('-')[1]
            user = get_user_from_id(user_id, payload)
            kyc = user.kyc_applications[0]
            kyc.kyc_status = 'REJECTED'

            # Update the message to show we've verified a user
            message_blocks = payload['message']['blocks']
            new_message_blocks = message_blocks[:len(message_blocks) - 1]
            new_message_blocks.append(dict(type='context', elements=[
                {"type": 'mrkdwn',
                 "text": ':x: *@{}* Rejected a verification or deferred to support.'.format(payload['user']['username'])}]))

            client.chat_update(
                channel=CHANNEL_ID,
                ts=payload["message"]["ts"],
                blocks=new_message_blocks
            )

            if user.phone:
                send_generic_message(to_phone=user.phone,
                                     message="Unfortunately, we couldn't verify your identity with the documents provided. Please open the Sempo app to retry or contact our customer support.")

            return make_response("", 200)

    elif payload["type"] == "dialog_submission":
        # The user has submitted the dialog

        user_id = payload['callback_id'].split('-')[1]
        user = get_user_from_id(user_id, payload)

        submission = payload['submission']
        kyc = user.kyc_applications[0]  # most recent

        kyc.first_name = submission['first_name']
        kyc.last_name = submission['last_name']
        kyc.dob = submission['date_of_birth']
        kyc.street_address = submission['address']

        db.session.flush()  # so that the response message updates user details

        message_blocks = generate_populated_message(user_id=user.id)
        new_message_blocks = message_blocks[:len(message_blocks) - 1]

        if payload['submission']['id_validity'] == 'valid':
            # Update the message to show that we're in the process of verifying a user
            new_message_blocks.append(dict(type='context', elements=[
                {"type": 'mrkdwn', "text": ':female-detective: Running AML checks...'}]))

            client.chat_update(
                channel=CHANNEL_ID,
                ts=payload["state"],
                blocks=new_message_blocks
            )

            result = run_namescam_aml_check(
                first_name=kyc.first_name,
                last_name=kyc.last_name,
                dob=kyc.dob,
                country=kyc.country
            )

            aml_result = json.loads(result.text)
            kyc.namescan_scan_id = aml_result['scan_id']

            match_rates = [x['match_rate'] for x in aml_result.get('persons', [])]
            avg_match_rate = 0
            if len(match_rates) > 0:
                avg_match_rate = sum(match_rates)/len(match_rates)

            if aml_result['number_of_matches'] == 0 or avg_match_rate < 50:
                # Instant Approval
                kyc.kyc_status = 'VERIFIED'
                return approve_user(new_message_blocks, username=payload['user']['name'], message_ts=payload["state"], phone=user.phone)

            else:
                # Manual Review Required
                generate_aml_message(parent_message_ts=payload["state"], aml_result=aml_result, avg_match_rate=avg_match_rate)

                new_message_blocks.append(dict(type='context', elements=[{"type": 'mrkdwn', "text": ':pencil: *@{}* Manual review needed.'.format(payload['user']['name'])}]))
                action_blocks = generate_actions(generate_approve_button(user_id), generate_deny_button(user_id))
                new_message_blocks.append(action_blocks)

                client.chat_update(
                    channel=CHANNEL_ID,
                    ts=payload["state"],
                    blocks=new_message_blocks
                )

                return make_response("", 200)

        else:
            # Update the message to indicate failed ID check.
            failure_options = {
                "non_valid": ":x: ID is not valid",
                "id_blurry": ":x: ID or selfie is too blurry",
                "no_match_selfie": ":x: ID does not match selfie"
            }
            new_message_blocks.append(dict(type='context', elements=[
                {"type": 'mrkdwn', "text": failure_options[payload['submission']['id_validity']]}]))

            kyc.kyc_status = 'INCOMPLETE'
            kyc.kyc_actions = [str(payload['submission']['id_validity'])]

            db.session.flush()

            client.chat_update(
                channel=CHANNEL_ID,
                ts=payload["state"],
                blocks=new_message_blocks
            )

    return make_response("", 200)

