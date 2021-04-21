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

@freeze_time("2020-02-15 13:30:00")
@pytest.fixture(scope='module')
def generate_timeseries_metrics(create_organisation):
    # Truncates date for timezone comparison to work any time of day you run the tests!
    # Adds 5 minutes to account for the small time difference between data generation and metric generation
    def truncate_date(date):
        return date.replace(hour=0, minute=5, second=0, microsecond=0)

    # Generates metrics over timeline
    # User1 and User2 made today
    user1 = create_transfer_account_user(first_name='Ricky',
                                    phone="+19025551234",
                                    organisation=create_organisation,
                                    roles=[('BENEFICIARY', 'beneficiary')])
    user1.created = truncate_date(user1.created)
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
    user2.created = truncate_date(user2.created)
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
    user3.created = truncate_date(user3.created)
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
    user4.created = truncate_date(user4.created)
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
    user5.created = truncate_date(user5.created)
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
    user6.created = truncate_date(user6.created)
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
    tu1.created = tu1.created - timedelta(days=15) + timedelta(hours = 22)
    tu2.created = tu1.created - timedelta(days=15) + timedelta(hours = 2)
    tu3.created = tu1.created - timedelta(days=15) + timedelta(hours = 1)

    p1 = make_payment_transfer(100,
        create_organisation.token,
        send_user=user1,
        send_transfer_account=user1.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    p1.created = truncate_date(p1.created) + timedelta(hours = 3)

    p2 = make_payment_transfer(25,
        create_organisation.token,
        send_user=user3,
        send_transfer_account=user3.default_transfer_account,
        receive_user=user4,
        receive_transfer_account=user4.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    p2.created = truncate_date(p2.created)
    p2.created = p2.created - timedelta(days=1) + timedelta(hours = 7)

    p3 = make_payment_transfer(5,
        create_organisation.token,
        send_user=user4,
        send_transfer_account=user4.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    p3.created = truncate_date(p3.created)
    p3.created = p3.created - timedelta(days=1) + timedelta(hours = 22)


    p4 = make_payment_transfer(20,
        create_organisation.token,
        send_user=user5,
        send_transfer_account=user5.default_transfer_account,
        receive_user=user6,
        receive_transfer_account=user6.default_transfer_account,
        transfer_use=str(int(tu3.id))
    )
    p4.created = truncate_date(p4.created)
    p4.created = p4.created - timedelta(days=4) + timedelta(hours = 1)

    p5 = make_payment_transfer(20,
        create_organisation.token,
        send_user=user6,
        send_transfer_account=user6.default_transfer_account,
        receive_user=user5,
        receive_transfer_account=user5.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    p5.created = truncate_date(p5.created)
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
    create_organisation.token.display_decimals = display_decimals
    def get_metrics(metric_type):
        return test_client.get(
            f'/api/v1/metrics/?metric_type={metric_type}&disable_cache=True&org={create_organisation.id}&group_by=recipient,account_type',
            headers=dict(
                Authorization=complete_admin_auth_token,
                Accept='application/json'
            ),
        )
    response = get_metrics(metric_type)
    assert response.status_code == status_code
    if response.json:
        returned_stats = response.json['data']['transfer_stats']
    else:
        returned_stats = None

    if status_code != 500:
        returned_stats['master_wallet_balance'] = 0
    if metric_type == 'credit_transfer':
        assert response.json == base_transfer
    elif metric_type == 'all' and display_decimals == 2:
        assert response.json == base_all
    elif metric_type == 'all' and display_decimals == 0:
        assert response.json == base_all_zero_decimals
    elif metric_type == 'user':
        assert response.json == base_participant

@pytest.mark.parametrize("metric_type, params, status_code, requested_metric, group_by, output_file, timezone", [
    ("all", None, 200, None, 'sender,account_type', 'all_by_account_type.json', 'UTC'),
    ("all", None, 200, None, 'colour,sender', 'all_by_sender_colour.json', 'UTC'),
    ("all", None, 200, None, 'colour,recipient', 'all_by_recipient_colour.json', 'UTC'),
    ("all", None, 200, None ,'sender,location', 'all_by_sender_location.json', 'UTC'),
    ("all", None, 200, None ,'recipient,location', 'all_by_recipient_location.json', 'UTC'),
    ("all", None, 200, None ,'sender,coordinates', 'all_by_coordinates.json', 'UTC'),
    ("all", None, 200, None, 'ungrouped', 'all_ungrouped.json', 'UTC'),
    ("all", "rounded_account_balance,sender(GT)(2)", 200, None, 'sender,account_type', 'all_by_account_type_filtered_by_sender.json', 'UTC'),
    ("all", "rounded_account_balance,recipient(GT)(2)", 200, None, 'sender,account_type', 'all_by_account_type_filtered_by_recipient.json', 'UTC'),
    ("all", "chips,sender(IN)(Barbecue)", 200, None, 'ungrouped', 'all_filtered_by_sender_chip_type.json', 'UTC'),
    ("all", "chips,recipient(IN)(Barbecue)", 200, None, 'ungrouped', 'all_filtered_by_recipient_chip_type.json', 'UTC'),
    ("all", "chips,sender(IN)(Dressed All Over):colour,sender(IN)(green)", 200, None, 'ungrouped', 'all_filtered_by_sender_chip_type_and_colour.json', 'UTC'),
    ("credit_transfer", None, 200, None, 'transfer_usage', 'credit_transfer_by_transfer_usage.json', 'UTC'),
    ("user", None, 200, None, 'sender,account_type', 'user_by_account_type.json', 'UTC'),
    ("credit_transfer", None, 200, None, 'transfer_type', 'credit_transfer_by_transfer_type.json', 'UTC'),
    ("all", None, 200, 'active_users', 'sender,account_type', 'requested_metric_active_users.json', 'UTC'),
    ("all", None, 500, None, 'transfer_usage', '', 'UTC'), # 500 because can't group all by transfer_usage 
    ("user", None, 500, None, 'transfer_usage', '', 'UTC'), # 500 because can't group user by transfer_usage
    ("user", 'transfer_amount(LT)(50)', 500, None, 'sender,account_type', '', 'UTC'), # 500 because can't filter user by transfer_amount
    ("all", 'transfer_amount(LT)(50)', 500, None, 'sender,account_type', '', 'UTC'), # 500 because can't filter all by transfer_amount
    ("all", None, 200, None ,'sender,location', 'all_by_location_halifax.json', 'America/Halifax'),
    ("all", None, 200, None, 'ungrouped', 'all_ungrouped_halifax.json', 'America/Halifax'),
])
def test_get_summed_metrics(
        test_client, complete_admin_auth_token, external_reserve_token, create_organisation, generate_timeseries_metrics,
        metric_type, params, status_code, requested_metric, group_by, output_file, timezone
):
    def ts_sort(ts):
        return sorted(ts, key=lambda item: isoparse(item['date']))

    def get_metrics(metric_type):
        p = f'&params={params}' if params else ''
        rm = f'&requested_metric={requested_metric}' if requested_metric else ''
        return test_client.get(
            f'/api/v1/metrics/?metric_type={metric_type}{p}&disable_cache=True&org={create_organisation.id}&group_by={group_by}{rm}',
            headers=dict(
                Authorization=complete_admin_auth_token,
                Accept='application/json'
            ),
        )
    create_organisation.timezone = timezone
    db.session.commit()
    response = get_metrics(metric_type)
    assert response.status_code == status_code

    if response.json:
        returned_stats = response.json['data']['transfer_stats']
    else:
        returned_stats = None
    if status_code == 200:
        script_directory = os.path.dirname(os.path.realpath(__file__))
        desired_output_file = os.path.join(script_directory, 'metrics_outputs', output_file)
        desired_output = json.loads(open(desired_output_file, 'r').read())
        for do in desired_output:
            if not isinstance(desired_output[do], dict) or "timeseries" not in desired_output[do]:
                assert returned_stats[do] == desired_output[do]
            else:
                assert returned_stats[do]['type'] == desired_output[do]['type']
                assert returned_stats[do]['aggregate'] == desired_output[do]['aggregate']
                for timeseries_category in returned_stats[do]['timeseries']:
                    sorted_returned_stats = ts_sort(returned_stats[do]['timeseries'][timeseries_category])
                    sorted_desired_stats = ts_sort(desired_output[do]['timeseries'][timeseries_category])
                    for idx in range(len(returned_stats[do]['timeseries'][timeseries_category])):
                        assert sorted_returned_stats[idx]['value'] == sorted_desired_stats[idx]['value']

@pytest.mark.parametrize("metric_type, status_code, hide_sender", [
    ("user", 200, False),
    ("all", 200, False),
    ("credit_transfer", 200, False),
    ("notarealmetrictype", 500, False),
    ("all", 200, True),
])
def test_get_metric_filters(test_client, complete_admin_auth_token, external_reserve_token,
                             metric_type, status_code, generate_timeseries_metrics, hide_sender):
    if hide_sender:
        db.session.query(CustomAttribute).first().group_visibility = MetricsVisibility.RECIPIENT

    db.session.commit()
    # Tests getting list of availible metrics filters from the /api/v1/metrics/filters endpoint
    response = test_client.get(
        f'/api/v1/metrics/filters/?metric_type={metric_type}',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
    )
    assert response.status_code == status_code
    filters = Filters()
    if status_code == 200:
        if metric_type == 'user':
            assert response.json['data']['filters'] == filters.USER_FILTERS
        elif metric_type == 'transfer':
            assert response.json['data']['filters'] == filters.TRANSFER_FILTERS
        assert response.json['data']['groups']['colour,recipient']['name'] == 'Colour'
        assert response.json['data']['groups']['colour,recipient']['sender_or_recipient'] == 'recipient'
        assert response.json['data']['groups']['colour,recipient']['table'] == 'custom_attribute_user_storage'
        if not hide_sender:
            assert response.json['data']['groups']['colour,sender']['name'] == 'Colour'
            assert response.json['data']['groups']['colour,sender']['sender_or_recipient'] == 'sender'
            assert response.json['data']['groups']['colour,sender']['table'] == 'custom_attribute_user_storage'
        else:
            assert 'colour,sender' not in response.json['data']['groups']

def test_clear_metrics_cache(test_client, complete_admin_auth_token):
    def clear_metrics():
        return test_client.post(
            f'/api/v1/metrics/clear_cache/',
            headers=dict(
                Authorization=complete_admin_auth_token,
                Accept='application/json'
            ),
        )
    
    # Do a non-test clear metrics to flush the cache
    clear_metrics()

    # Create 4 fake metrics
    red.set('2_metrics_fake_metric1', '123')
    red.set('2_metrics_fake_metric2', '123')
    red.set('2_metrics_fake_metric3', '123')
    red.set('2_metrics_fake_metric4', '123')

    # Clear them for reals now
    response = clear_metrics()

    # Make sure that 4 metrics are removed from the cache
    assert response.json['data']['removed_entries'] == 4
    
    # And check that they're well and truly gone from the cache!
    assert not red.get('2_metrics_fake_metric1') 
    assert not red.get('2_metrics_fake_metric2') 
    assert not red.get('2_metrics_fake_metric3') 
    assert not red.get('2_metrics_fake_metric4') 
