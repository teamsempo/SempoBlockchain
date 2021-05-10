import boto3, jinja2, os
from urllib import parse
from flask import request, current_app
from server import pusher_client
from server.utils.executor import standard_executor_job, add_after_request_executor_job

def send_transfer_update_email(email_address, transfer_info, latest_status):
    TEXT_TEMPLATE_FILE = 'transfer_update_email.txt'
    text_template = get_email_template(TEXT_TEMPLATE_FILE)
    textbody = text_template.render(
        amount=transfer_info['sourceAmount'],
        transfer_id=transfer_info['id'],
        currency=transfer_info['sourceCurrency'],
        status=latest_status['statusDetail'],
    )

    HTML_TEMPLATE_FILE = 'transfer_update_email.html'
    html_template = get_email_template(HTML_TEMPLATE_FILE)
    htmlbody = html_template.render(
        amount=transfer_info['sourceAmount'],
        transfer_id=transfer_info['id'],
        currency=transfer_info['sourceCurrency'],
        status=latest_status['statusDetail'],
    )
    add_after_request_executor_job(ses_email_handler, [email_address, 'Sempo: Transfer Update', textbody, htmlbody])


def send_bank_transfer_email(email_address, charge_info):
    TEXT_TEMPLATE_FILE = 'bank_transfer_email.txt'
    text_template = get_email_template(TEXT_TEMPLATE_FILE)
    bank = charge_info['wireDetails']
    textbody = text_template.render(
        amount=charge_info['amount'],
        transfer_id=charge_info['id'],
        currency=charge_info['currency'],
        instructions=bank['instructions'],
        account_number=bank['accountNumber'],
        routing_number=bank['routingNumber'],
        swift_code=bank['swiftCode'],
        account_type=bank['accountType'],
        bank_address=bank['bankAddress'],
        beneficiary=bank['beneficiary']
    )

    HTML_TEMPLATE_FILE = 'bank_transfer_email.html'
    html_template = get_email_template(HTML_TEMPLATE_FILE)
    htmlbody = html_template.render(
        amount=charge_info['amount'],
        transfer_id=charge_info['id'],
        currency=charge_info['currency'],
        instructions=bank['instructions'],
        account_number=bank['accountNumber'],
        routing_number=bank['routingNumber'],
        swift_code=bank['swiftCode'],
        account_type=bank['accountType'],
        bank_address=bank['bankAddress'],
        beneficiary=bank['beneficiary']
    )

    add_after_request_executor_job(ses_email_handler, [email_address, 'Sempo: Fund your wallet', textbody, htmlbody])

def send_invite_email(invite, organisation):

    TEMPLATE_FILE = 'invite_email.txt'
    template = get_email_template(TEMPLATE_FILE)
    email = parse.quote(invite.email, safe='')
    body = template.render(host=current_app.config['APP_HOST'],
                           organisation_name=organisation.name,
                           referral_code=invite.referral_code,
                           email=email)

    add_after_request_executor_job(ses_email_handler, [invite.email, 'Sempo: Invite to Join!', body])

def send_invite_email_to_existing_user(organisation, email_address):

    TEMPLATE_FILE = 'invite_existing_user_email.txt'
    template = get_email_template(TEMPLATE_FILE)
    body = template.render(host=current_app.config['APP_HOST'],
                           organisation_name=organisation.name)

    add_after_request_executor_job(ses_email_handler, [email_address, 'Sempo: Added to new Organisation!', body])

def send_export_email(file_url, email_address):

    TEMPLATE_FILE = 'export_email.txt'
    template = get_email_template(TEMPLATE_FILE)
    body = template.render(file_url=file_url, deployment=current_app.config['DEPLOYMENT_NAME'])

    add_after_request_executor_job(ses_email_handler, [email_address, 'Sempo: Your export is ready!', body])

def send_activation_email(activation_token, email_address):

    TEXT_TEMPLATE_FILE = 'account_activation_email.txt'
    text_template = get_email_template(TEXT_TEMPLATE_FILE)
    textbody = text_template.render(host=current_app.config['APP_HOST'], activation_token=activation_token)

    HTML_TEMPLATE_FILE = 'account_activation_email.html'
    html_template = get_email_template(HTML_TEMPLATE_FILE)
    htmlbody = html_template.render(host=current_app.config['APP_HOST'], activation_token=activation_token)

    add_after_request_executor_job(ses_email_handler, [email_address, 'Sempo: Activate your account', textbody, htmlbody])

def send_reset_email(reset_token, email_address):
    TEMPLATE_FILE = 'password_reset_email.txt'
    template = get_email_template(TEMPLATE_FILE)
    body = template.render(host=current_app.config['APP_HOST'], reset_token=reset_token)
    add_after_request_executor_job(ses_email_handler, [email_address, 'Sempo Password Reset', body])

def get_email_template(TEMPLATE_FILE):
    searchpath = os.path.join(current_app.config['BASEDIR'], "templates")

    templateLoader = jinja2.FileSystemLoader(searchpath=searchpath)
    templateEnv = jinja2.Environment(loader=templateLoader)

    return templateEnv.get_template(TEMPLATE_FILE)

@standard_executor_job
def ses_email_handler(recipient, subject, textbody, htmlbody = None):
    sender = "admin@withsempo.com"

    awsregion = "us-west-2"
    htmlbody = htmlbody or textbody
    charset = "UTF-8"

    if not current_app.config['IS_PRODUCTION']:
        print(f"Email Sent to {recipient} "
              f"\nSubject:"
              f"\n{subject}"
              f"\nBody:"
              f"\n{textbody}")

    if not current_app.config['IS_TEST']:

        # Create a new SES resource and specify a region.
        client = boto3.client('ses',
                            aws_access_key_id= current_app.config['AWS_SES_KEY_ID'],
                            aws_secret_access_key=current_app.config['AWS_SES_SECRET'],
                              region_name=awsregion)

        # Try to send the email.
        try:
            #Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        recipient,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': charset,
                            'Data': htmlbody,
                        },
                        'Text': {
                            'Charset': charset,
                            'Data': textbody,
                        },
                    },
                    'Subject': {
                        'Charset': charset,
                        'Data': subject,
                    },
                },
                Source=sender,
            )

            print(response)
        # Display an error if something goes wrong.
        except Exception as e:
            print ("Error: ", e)
        else:
            print ("Email sent!")
