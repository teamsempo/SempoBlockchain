from flask import current_app
from server import pusher_client, sentry
from server.schemas import credit_transfer_schema
from server.utils import credit_transfer


def push_admin_credit_transfer(transfer):
    new_transfer = credit_transfer_schema.dump(transfer).data

    for org in transfer.organisations:
        pusher_channel = current_app.config['PUSHER_ENV_CHANNEL'] + '-' + org.name + '-' + str(org.id)
        try:
            pusher_client.trigger(
                pusher_channel,
                'credit_transfer',
                {'credit_transfer': new_transfer}
            )
        except Exception as e:
            print(e)
            sentry.captureException()

def push_user_transfer_confirmation(receive_user, transfer_random_key):
    try:
        pusher_client.trigger(
            'private-user-{}-{}'.format(current_app.config['DEPLOYMENT_NAME'], receive_user.id),
            'payment_confirmed',
            {'transfer_random_key': transfer_random_key}
        )
    except Exception as e:
        print(e)
        sentry.captureException()