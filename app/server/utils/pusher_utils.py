import sentry_sdk

from flask import current_app
from server import pusher_client
from server.utils.executor import standard_executor_job, add_after_request_executor_job
from server.schemas import credit_transfer_schema
from server.utils import credit_transfer
from server.utils import misc

# Pusher currently only allowes batches of 10 at a time
# https://pusher.com/docs/channels/library_auth_reference/rest-api#post-batch-events-trigger-multiple-events-
PUSHER_MAX_BATCH_SIZE = 10

@standard_executor_job
def async_pusher_trigger(*args, **kwargs):
    pusher_client.trigger(*args, **kwargs)

@standard_executor_job
def async_pusher_trigger_batch(*args, **kwargs):
    pusher_client.trigger_batch(*args, **kwargs)

def push_admin_credit_transfer(transfers):
    # If we only get one transfer, make it a list
    if not isinstance(transfers, list):
        transfers = [transfers]

    # Build prepared list of transfers we want to send
    pusher_batch_payload = []
    for transfer in transfers:
        if hasattr(transfer, 'organisations'):
            for org in transfer.organisations:
                pusher_transfer_payload = {}
                pusher_transfer_payload['data'] = {}
                pusher_transfer_payload['data']['credit_transfer'] = credit_transfer_schema.dump(transfer).data
                pusher_transfer_payload['name'] = 'credit_transfer'
                pusher_transfer_payload['channel'] = current_app.config['PUSHER_ENV_CHANNEL'] + '-' + str(org.id)
                pusher_batch_payload.append(pusher_transfer_payload)

    # Break the list of prepared transfers into MAX_BATCH_SIZE chunks and send each batch to the API
    for pusher_payload_chunk in misc.chunk_list(pusher_batch_payload, PUSHER_MAX_BATCH_SIZE):
        try:
            add_after_request_executor_job(async_pusher_trigger_batch, [pusher_payload_chunk])
        except Exception as e:
            print(e)
            sentry_sdk.capture_exception(e)

def push_user_transfer_confirmation(receive_user, transfer_random_key):
    try:
        add_after_request_executor_job(async_pusher_trigger, ['private-user-{}-{}'.format(current_app.config['DEPLOYMENT_NAME'], receive_user.id),\
             'payment_confirmed',\
                {'transfer_random_key': transfer_random_key}])

    except Exception as e:
        print(e)
        sentry_sdk.capture_exception(e)
