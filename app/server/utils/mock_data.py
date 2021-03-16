import sys
import os
import random
from uuid import uuid4
from flask import g
from datetime import timedelta, datetime

# Needed since this gets used from the setup script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import config

import math
from decimal import Decimal

from server import create_app, db, bt
from server.models.token import Token, TokenType
from server.models.organisation import Organisation
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.exchange import ExchangeContract, Exchange
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferModeEnum

from server.utils.user import create_transfer_account_user, set_custom_attributes


data_size_options = {
    'small': {'users': 15, 'transfers': 30},
    'medium': {'users': 150, 'transfers': 300},
    'large': {'users': 1000, 'transfers': 1000}
}

ADJECTIVES = [
    'Merry', 'Bold', 'Hungry', 'Trustworthy', 'Valued', 'Free',
    'Frequentist', 'Young', 'Agile', 'Happy', 'Safe', 'Cool',
    'Bayesian', 'Willing', 'Quick', 'Unassuming', 'Contemplative',
    'Adaptive', 'Brave', 'Careful', 'Daring', 'Elegent', 'Friendly', 'Generous', 'Humorous', 'Ingenious',
    'Legendary', 'Magnificent', 'Noble', 'Original', 'Perceptive', 'Quixotic', 'Regal', 'Smart', 'Talented',
    'Unshakable', 'Versatile', 'Wonderful', 'Zen'
]

ANIMALS = [
    'Armadilo', 'Badger', 'Cassowary', 'Dingo', 'Elephant', 'Frog', 'Giraffe', 'Hippo', 'Iguana', 'Jaguar',
    'Kangaroo', 'Lion', 'Manatee', 'Narwhal', 'Octopus', 'Panther', 'Quail', 'Rooster', 'Salamander', 'Tiger',
    'Uakari', 'Vole', 'Walrus', 'Xeme', 'Yeti', 'Zebra', 'Kitty', 'Otter', 'Dogo', 'Panda', 'Chimp'
]

LOCATIONS = [
    ('Mount Agung', -8.343, 115.507),
    ('Mount Mayon', 13.254, 123.686),
    ('Ventura', 34.370, -119.139),
    ('Halba', 34.544, 36.079),
    ('Mkalles', 33.867, 35.542),
    ('Bardarash', 36.501, 43.584),
    ('Sofokleous', 37.981, 23.726),
    ('Melemaat', -17.678, 168.259),
    ('Pango', -17.775, 168.290),
    ('White Sands', -19.501, 169.445),
    ('Malapoa', -17.723, 168.305),
    ('Kibera', -1.312, 36.781),
    ('Miyani', -3.668, 39.516),
]

def rand_bool(probabily_of_true):
    return random.random() < probabily_of_true

def create_users(number_of_users, transfer_usages, org, created_offset=0):
    i = 0
    users_by_location = {}

    for i in range(number_of_users):

        print(f'Created user {i}')

        user, behavior = create_transfer_user(
            email=f'user_{i}@org{org.id}.com',
            transfer_usages=transfer_usages,
            organisation=org,
            created_offset=created_offset
        )

        location = user.location

        if location not in users_by_location:
            users_by_location[location] = []

        users_by_location[location].append((user, behavior))

        db.session.commit()
    return users_by_location


def create_transfer_user(email, transfer_usages, organisation, created_offset):

    first_name, middle_name = random.sample(ADJECTIVES, 2)

    last_name = f'{middle_name} {random.choice(ANIMALS)}'

    is_beneficiary = rand_bool(0.9)
    if is_beneficiary:
        roles = roles=[('BENEFICIARY', 'beneficiary')]
    else:
        roles=[('VENDOR', 'vendor')]

    phone = '+1' + ''.join([str(random.randint(0,10)) for i in range(0, 10)])

    user = create_transfer_account_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        organisation=organisation,
        roles=roles,
    )

    # Set the created date to the first day
    user.created = datetime.utcnow() - timedelta(days=created_offset)

    location, lat, lng = random.choice(LOCATIONS)

    # Assign the user to a random location and jitter the latlong slightly
    user._location = location
    user.lat = lat + random.random()/100
    user.lng = lng + random.random()/100

    attribute_dict = {'custom_attributes': {}}

    attribute_dict['custom_attributes']['gender'] = random.choice(['male', 'female'])

    set_custom_attributes(attribute_dict, user)

    if not is_beneficiary:
        bu = random.choice(transfer_usages)
        user.business_usage = bu

    # Create purchase behavior profile
    behavior = {}

    # 10% chance the user's purchase will always include a particular category
    single_item_purchaser = rand_bool(0.1)
    if single_item_purchaser:
        item = random.choice(transfer_usages)
        behavior['purchase_item'] = item
    else:
        behavior['purchase_item'] = None

    # A fixed likelihood that this user will actually make a purchase if selected.
    behavior['spend_probability'] = random.random()

    # The likelihood that the user's purchase is at a different location
    behavior['out_of_town_probability'] = random.random()/3

    return user, behavior


def create_disbursments(users_by_location, admin_user, token, amount_to_disburse, created_offset=0):
    print('Disbursing to users')

    for location, users in users_by_location.items():

        for user, behavior in users:
            print(f'Disbursing to user {user.id}')
            create_transfer(
                amount=amount_to_disburse,
                sender_user=admin_user,
                recipient_user=user,
                token=token,
                subtype=TransferSubTypeEnum.DISBURSEMENT,
                created_offset=created_offset,
                transfer_mode=TransferModeEnum.WEB
            )


def create_payments(users_by_location, number_of_transfers, time_period_days, transfer_usages, token):

    transfer_count_per_day = [0 for i in range(0, time_period_days)]

    # Randomly allocate our desired number of transfers across the date range
    for _ in range(0, number_of_transfers):
        d = random.randint(0, time_period_days - 1)
        transfer_count_per_day[d] += 1

    transfer_list = []

    locations = list(users_by_location.keys())

    for day_index, required_transfers in enumerate(transfer_count_per_day):
        i = 0
        for i in range(required_transfers):
            print(f'Creating day {day_index}, transfer {i}')

            found_a_sender = False

            sender_loc = random.choice(locations)

            sender_user = sender_behavior = None
            spend_amount = 0

            # Keep on picking users until one passes the 'spend probability' test
            while not found_a_sender:
                sender_user, sender_behavior = random.choice(users_by_location[sender_loc])

                if rand_bool(sender_behavior['spend_probability']):

                    sender_balance = sender_user.default_transfer_account.balance

                    spend_amount = math.floor(Decimal(random.random()) * sender_balance * 100) / 100

                    if spend_amount > 0:
                        found_a_sender = True

            if sender_behavior['purchase_item']:
                tu = [sender_behavior['purchase_item']]
            else:
                tu = [random.choice(transfer_usages)]

            # 20% chance the purchase contains another usage category
            further_usages = rand_bool(0.2)
            while further_usages:
                tu.append(random.choice(transfer_usages))
                further_usages = rand_bool(0.2)

            if rand_bool(sender_behavior['out_of_town_probability']):
                recipient_loc = random.choice(locations)
            else:
                recipient_loc = sender_loc

            recipient_user, _ = random.choice(users_by_location[recipient_loc])

            transfer = create_transfer(
                amount=spend_amount,
                sender_user=sender_user,
                recipient_user=recipient_user,
                token=token,
                transfer_usages=tu,
                created_offset=time_period_days - day_index - 1,
                transfer_mode=random.choice([TransferModeEnum.MOBILE, TransferModeEnum.NFC, TransferModeEnum.USSD])
            )

            transfer_list.append(transfer)

        print(f'Finished Day {day_index}')
        # Commit to prevent memory errors with large numbers of txns counts
        db.session.commit()

    return transfer_list


def create_transfer(
        amount,
        sender_user,
        recipient_user,
        token,
        subtype=TransferSubTypeEnum.STANDARD,
        transfer_usages=None,
        created_offset=0,
        transfer_mode=None
):
    transfer = CreditTransfer(
        amount=amount,
        sender_user=sender_user,
        recipient_user=recipient_user,
        token=token,
        uuid=str(uuid4()))

    db.session.add(transfer)
    # Mimics before_request hook
    g.pending_transactions = []

    if transfer_usages:
        transfer.transfer_usages = transfer_usages

    transfer.resolve_as_complete_and_trigger_blockchain()

    transfer.transfer_type = TransferTypeEnum.PAYMENT
    transfer.transfer_subtype = subtype
    transfer.transfer_mode = transfer_mode

    transfer.created = datetime.utcnow() - timedelta(days=created_offset)

    # Commit to prevent memory errors with large numbers of txns counts
    db.session.commit()

    # Mimic after request hook midway through process
    for transaction, queue in g.pending_transactions:
        transaction.send_blockchain_payload_to_worker(queue=queue)

    return transfer



def _get_or_create_model_object(obj_class: db.Model, filter_kwargs: dict, **kwargs):

    instance = obj_class.query.filter_by(**filter_kwargs).first()

    if instance:
        return instance
    else:
        instance = obj_class(**{**filter_kwargs, **kwargs})
        db.session.add(instance)
        return instance


def create_dev_data(organisation_id, data_size):
    app = create_app(skip_create_filters=True)
    ctx = app.app_context()
    ctx.push()

    size_dict = data_size_options[data_size]

    # To simplify creation, we set the flask context to show all model data
    g.show_all = True

    organisation = Organisation.query.get(organisation_id)

    if organisation is None:
        raise Exception(f"Organisation not found for ID {organisation_id}")

    admin_user = User.query.filter_by(email=str('admin@acme.org').lower()).first()

    token = organisation.token

    print('Create a list of users with a different business usage id ')
    transfer_usages = TransferUsage.query.all()

    users_by_location = create_users(size_dict['users'], transfer_usages, organisation)

    print('Making Transfers')
    create_disbursments(users_by_location, admin_user, token, 1000)
    create_payments(users_by_location, size_dict['transfers'], 14, transfer_usages, token)

    # TODO: Create Exchanges between different currencies

    db.session.commit()
    ctx.pop()


if __name__ == '__main__':
    # The utility scrips here can be called outside of the
    # Creates dev data for the master org
    create_dev_data(1, 'small')

    if len(sys.argv) > 1:
        # Creates dev data for the secondary org
        create_dev_data(2, sys.argv[1])

