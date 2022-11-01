import pytest
from freezegun import freeze_time
from server.models.transfer_usage import TransferUsage
from server.models.custom_attribute import CustomAttribute, MetricsVisibility
from server.utils.transfer_filter import Filters
from server.utils.credit_transfer import make_payment_transfer
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server import db, red
import json
import os
from datetime import datetime, timedelta
from dateutil.parser import isoparse

zero_time = datetime(2019, 1, 15)
@pytest.fixture(scope='module')
def generate_timeseries_metrics(create_organisation):
    # Generates metrics over timeline
    # User1 and User2 made today
    create_organisation.queried_org_level_transfer_account.set_balance_offset(10000000000)
    user1 = create_transfer_account_user(first_name='Ricky',
                                    phone="+19025551234",
                                    organisation=create_organisation,
                                    roles=[('BENEFICIARY', 'beneficiary')])
    user1.created = zero_time
    user1.default_transfer_account.is_approved = True
    user1.default_transfer_account._make_initial_disbursement(100, True)
    user1._location = 'Sunnyvale'
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['colour'] = 'red'
    attribute_dict['custom_attributes']['chips'] = 'Dressed All Over'
    set_custom_attributes(attribute_dict, user1)
    user1.lat = 44.675447
    user1.lng = -63.594995

    user2 = create_transfer_account_user(first_name='Bubbles',
                                    phone="+19025551235",
                                    organisation=create_organisation)
    user2.created = zero_time
    user2.default_transfer_account.is_approved = True
    user2.default_transfer_account._make_initial_disbursement(200, True)
    user2._location = 'Sunnyvale'
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['colour'] = 'red'
    attribute_dict['custom_attributes']['chips'] = 'Chicken'
    user2.lat = 44.675447
    user2.lng = -63.594995

    set_custom_attributes(attribute_dict, user2)

    # user3 made yesterday
    user3 = create_transfer_account_user(first_name='Julian',
                                    phone="+19025531230",
                                    organisation=create_organisation)
    user3.default_transfer_account.is_approved = True
    disburse = user3.default_transfer_account._make_initial_disbursement(210, True)
    user3.created = zero_time
    user3.created = user3.created - timedelta(days=1) + timedelta(hours=6)
    disburse.created = user3.created - timedelta(days=1) + timedelta(hours=3)
    user3._location = 'Dartmouth'
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['colour'] = 'blue'
    attribute_dict['custom_attributes']['chips'] = 'Barbecue'
    set_custom_attributes(attribute_dict, user3)
    user3.lat = 44.668055
    user3.lng = -63.580829

    # user4 made 4 days ago
    user4 = create_transfer_account_user(first_name='Randy',
                                    phone="+19025511230",
                                    organisation=create_organisation)
    user4.created = zero_time
    user4.default_transfer_account.is_approved = True
    disburse = user4.default_transfer_account._make_initial_disbursement(201, True)
    user4.created = user4.created - timedelta(days=4) + timedelta(hours = 23)
    disburse.created = user4.created - timedelta(days=4) + timedelta(hours = 1)
    user4._location = 'Lower Sackville'
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['colour'] = 'blue'
    attribute_dict['custom_attributes']['chips'] = 'Barbecue'
    set_custom_attributes(attribute_dict, user4)
    user4.lat = 44.770061
    user4.lng = -63.692723

    # user5/user6 made 10 days ago
    user5 = create_transfer_account_user(first_name='Cory',
                                    phone="+19011531230",
                                    organisation=create_organisation)
    user5.created = zero_time
    user5.default_transfer_account.is_approved = True
    disburse = user5.default_transfer_account._make_initial_disbursement(202, True)
    user5.created = user5.created - timedelta(days=10) + timedelta(hours = 2)
    disburse.created = user5.created - timedelta(days=10) + timedelta(hours = 5)
    user5._location = 'Truro'
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['colour'] = 'green'
    attribute_dict['custom_attributes']['chips'] = 'Dressed All Over'
    set_custom_attributes(attribute_dict, user5)
    user5.lat = 45.368075
    user5.lng = -63.256207


    user6 = create_transfer_account_user(first_name='Trevor',
                                    phone="+19025111230",
                                    organisation=create_organisation)
    user6.created = zero_time
    user6.default_transfer_account.is_approved = True
    disburse = user6.default_transfer_account._make_initial_disbursement(204, True)
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['colour'] = 'red'
    attribute_dict['custom_attributes']['chips'] = 'Jalapeno'
    set_custom_attributes(attribute_dict, user6)
    user6.lat = 44.368363
    user6.lng = -64.526330

    db.session.commit()
    tu1 = TransferUsage.find_or_create("Pepperoni")
    tu2 = TransferUsage.find_or_create("Jalepeno Chips")
    tu3 = TransferUsage.find_or_create("Shopping Carts")
    tu1.created = zero_time - timedelta(days=15) + timedelta(hours = 22)
    tu2.created = zero_time - timedelta(days=15) + timedelta(hours = 2)
    tu3.created = zero_time - timedelta(days=15) + timedelta(hours = 1)

    p1 = make_payment_transfer(100,
        create_organisation.token,
        send_user=user1,
        send_transfer_account=user1.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    p1.created = zero_time + timedelta(hours = 3)

    p2 = make_payment_transfer(25,
        create_organisation.token,
        send_user=user3,
        send_transfer_account=user3.default_transfer_account,
        receive_user=user4,
        receive_transfer_account=user4.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    p2.created = zero_time
    p2.created = p2.created - timedelta(days=1) + timedelta(hours = 7)

    p3 = make_payment_transfer(5,
        create_organisation.token,
        send_user=user4,
        send_transfer_account=user4.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    p3.created = zero_time
    p3.created = p3.created - timedelta(days=1) + timedelta(hours = 22)


    p4 = make_payment_transfer(20,
        create_organisation.token,
        send_user=user5,
        send_transfer_account=user5.default_transfer_account,
        receive_user=user6,
        receive_transfer_account=user6.default_transfer_account,
        transfer_use=str(int(tu3.id))
    )
    p4.created = zero_time
    p4.created = p4.created - timedelta(days=4) + timedelta(hours = 1)

    p5 = make_payment_transfer(20,
        create_organisation.token,
        send_user=user6,
        send_transfer_account=user6.default_transfer_account,
        receive_user=user5,
        receive_transfer_account=user5.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    p5.created = zero_time
    p5.created = p5.created - timedelta(days=6) + timedelta(hours = 23)
    db.session.commit()

base_participant = {
    'data': {
        'transfer_stats': 
        {'active_filters': [], 
        'active_group_by': 'recipient,account_type', 
        'active_users': {'aggregate': {'percent_change': None, 'total': 0}, 
        'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
        'mandatory_filter': {}, 
        'master_wallet_balance': 0, 
        'total_population_cumulative': {'aggregate': {'percent_change': 0.0, 'total': 1}, 
        'timeseries': {}, 
        'type': {'display_decimals': 0, 'value_type': 'count'}}, 
        'users_created': {'aggregate': {'percent_change': 0.0, 'total': 1}, 
        'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}}}, 
        'message': 'Successfully Loaded.', 
        'status': 'success'
    }


base_all = {
    'data': {
        'transfer_stats': 
        {'active_filters': [], 
        'active_group_by': 'recipient,account_type', 
        'active_users': {'aggregate': {'percent_change': None, 'total': 0}, 
        'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
        'all_payments_volume': {'aggregate': {'percent_change': None, 'total': 0}, 
        'timeseries': {}, 'type': {'currency_name': 'AUD Reserve Token', 'currency_symbol': 'AUD', 'display_decimals': 2, 'value_type': 'currency'}}, 
        'daily_transaction_count': {'aggregate': {'percent_change': None, 'total': 0}, 
        'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
        'mandatory_filter': {}, 
        'master_wallet_balance': 0, 
        'total_distributed': 0.0, 
        'total_population_cumulative': {'aggregate': {'percent_change': 0.0, 'total': 1}, 
        'timeseries': {}, 
        'type': {'display_decimals': 0, 'value_type': 'count'}}, 
        'total_reclaimed': 0.0, 
        'total_withdrawn': 0.0, 
        'trades_per_user': {'aggregate': {'percent_change': None, 'total': 0.0}, 'timeseries': {}, 
        'type': {'display_decimals': 2, 'value_type': 'count_average'}}, 
        'transfer_amount_per_user': {'aggregate': {'percent_change': None, 'total': 0.0}, 
        'timeseries': {}, 
        'type': {'currency_name': 'AUD Reserve Token', 'currency_symbol': 'AUD', 'display_decimals': 2, 'value_type': 'currency'}}, 
        'users_created': {'aggregate': {'percent_change': 0.0, 'total': 1}, 
        'timeseries': {}, 
        'type': {'display_decimals': 0, 'value_type': 'count'}}, 
        'users_who_made_purchase': {'aggregate': {'percent_change': None, 'total': 0}, 
        'timeseries': {}, 
        'type': {'display_decimals': 0, 'value_type': 'count'}}}}, 
        'message': 'Successfully Loaded.', 
        'status': 'success'
    }

base_all_zero_decimals = {'data': 
    {'transfer_stats': 
    {'active_filters': [], 
    'active_group_by': 'recipient,account_type', 
    'active_users': {'aggregate': {'percent_change': None, 'total': 0}, 'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
    'all_payments_volume': {'aggregate': {'percent_change': None, 'total': 0}, 
    'timeseries': {}, 
    'type': {'currency_name': 'AUD Reserve Token', 'currency_symbol': 'AUD', 'display_decimals': 0, 'value_type': 'currency'}}, 
    'daily_transaction_count': {'aggregate': {'percent_change': None, 'total': 0}, 'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
    'mandatory_filter': {}, 
    'master_wallet_balance': 0, 
    'total_distributed': 0.0, 
    'total_population_cumulative': {'aggregate': {'percent_change': 0.0, 'total': 1}, 'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
    'total_reclaimed': 0.0, 
    'total_withdrawn': 0.0, 
    'trades_per_user': {'aggregate': {'percent_change': None, 'total': 0.0}, 'timeseries': {}, 
    'type': {'display_decimals': 2, 'value_type': 'count_average'}}, 
    'transfer_amount_per_user': {'aggregate': {'percent_change': None, 'total': 0.0}, 
    'timeseries': {}, 
    'type': {'currency_name': 'AUD Reserve Token', 'currency_symbol': 'AUD', 'display_decimals': 0, 'value_type': 'currency'}}, 
    'users_created': {'aggregate': {'percent_change': 0.0, 'total': 1}, 
    'timeseries': {}, 
    'type': {'display_decimals': 0, 'value_type': 'count'}}, 
    'users_who_made_purchase': {'aggregate': {'percent_change': None, 'total': 0}, 'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}}}, 
    'message': 'Successfully Loaded.', 
    'status': 'success'
    }

base_transfer = {'data': 
    {'transfer_stats': 
    {'active_filters': [], 
    'active_group_by': 'recipient,account_type', 
    'all_payments_volume': 
        {'aggregate': {'percent_change': None, 'total': 0}, 'timeseries': {}, 'type': {'currency_name': 'AUD Reserve Token', 'currency_symbol': 'AUD', 'display_decimals': 2, 'value_type': 'currency'}}, 
    'daily_transaction_count': 
        {'aggregate': {'percent_change': None, 'total': 0}, 'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}, 
    'mandatory_filter': {}, 
    'master_wallet_balance': 0, 
    'total_distributed': 0.0, 
    'total_reclaimed': 0.0,
    'total_withdrawn': 0.0,
    'trades_per_user': 
        {'aggregate': {'percent_change': None, 'total': 0.0}, 'timeseries': {}, 'type': {'display_decimals': 2, 'value_type': 'count_average'}}, 
    'transfer_amount_per_user': 
        {'aggregate': {'percent_change': None, 'total': 0.0}, 'timeseries': {}, 'type': {'currency_name': 'AUD Reserve Token', 'currency_symbol': 'AUD', 'display_decimals': 2, 'value_type': 'currency'}}, 
    'users_who_made_purchase': 
        {'aggregate': {'percent_change': None, 'total': 0}, 'timeseries': {}, 'type': {'display_decimals': 0, 'value_type': 'count'}}}}, 
    'message': 'Successfully Loaded.', 
    'status': 'success'}

@pytest.mark.parametrize("metric_type, status_code, display_decimals", [
    ("user", 200, 2),
    ("all", 200, 2),
    ("all", 200, 0),
    ("credit_transfer", 200, 2),
    ("notarealmetrictype", 500, 2),
])
def test_get_zero_metrics(test_client, complete_admin_auth_token, external_reserve_token, create_organisation,
                             metric_type, status_code, display_decimals):
    print('pass')