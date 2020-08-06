import pytest
from server.models.transfer_usage import TransferUsage
from server.utils.transfer_filter import ALL_FILTERS, USER_FILTERS
from server.utils.credit_transfer import make_payment_transfer
from server.utils.user import create_transfer_account_user, set_custom_attributes
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server import db
import json
import os
from datetime import datetime, timedelta

@pytest.fixture(scope='module')
def generate_timeseries_metrics(create_organisation):
    # Generates metrics over timeline
    
    # User1 and User2 made today
    user1 = create_transfer_account_user(first_name='Ricky',
                                    phone="+19025551234",
                                    organisation=create_organisation,
                                    is_beneficiary=True)
    user1.default_transfer_account.is_approved = True
    user1.default_transfer_account._make_initial_disbursement(100, True)

    user2 = create_transfer_account_user(first_name='Bubbles',
                                    phone="+19025551235",
                                    organisation=create_organisation)
    user2.default_transfer_account.is_approved = True
    user2.default_transfer_account._make_initial_disbursement(200, True)

    # user3 made yesterday
    user3 = create_transfer_account_user(first_name='Julian',
                                    phone="+19025531230",
                                    organisation=create_organisation)
    user3.default_transfer_account.is_approved = True
    disburse = user3.default_transfer_account._make_initial_disbursement(210, True)
    user3.created = user3.created - timedelta(days=1)
    disburse.created = user3.created - timedelta(days=1)

    # user4 made 4 days ago
    user4 = create_transfer_account_user(first_name='Randy',
                                    phone="+19025511230",
                                    organisation=create_organisation)
    user4.default_transfer_account.is_approved = True
    disburse = user4.default_transfer_account._make_initial_disbursement(201, True)
    user4.created = user4.created - timedelta(days=4)
    disburse.created = user4.created - timedelta(days=4)

    # user5/user6 made 10 days ago
    user5 = create_transfer_account_user(first_name='Cory',
                                    phone="+19011531230",
                                    organisation=create_organisation)
    user5.default_transfer_account.is_approved = True
    disburse = user5.default_transfer_account._make_initial_disbursement(202, True)
    user5.created = user5.created - timedelta(days=10)
    disburse.created = user5.created - timedelta(days=10)

    user6 = create_transfer_account_user(first_name='Trevor',
                                    phone="+19025111230",
                                    organisation=create_organisation)
    user6.default_transfer_account.is_approved = True
    disburse = user6.default_transfer_account._make_initial_disbursement(204, True)
    user6.created = user6.created - timedelta(days=10)
    disburse.created = user6.created - timedelta(days=10)

    db.session.commit()

    tu1 = TransferUsage.find_or_create("Pepperoni")
    tu2 = TransferUsage.find_or_create("Jalepeno Chips")
    tu3 = TransferUsage.find_or_create("Shopping Carts")
    tu1.created = tu1.created - timedelta(days=15)
    tu2.created = tu1.created - timedelta(days=15)
    tu3.created = tu1.created - timedelta(days=15)

    p1 = make_payment_transfer(100,
        create_organisation.token,
        send_user=user1,
        send_transfer_account=user1.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )

    p2 = make_payment_transfer(25,
        create_organisation.token,
        send_user=user3,
        send_transfer_account=user3.default_transfer_account,
        receive_user=user4,
        receive_transfer_account=user4.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    p2.created = p2.created - timedelta(days=1)

    p3 = make_payment_transfer(5,
        create_organisation.token,
        send_user=user4,
        send_transfer_account=user4.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    p3.created = p3.created - timedelta(days=1)

    p4 = make_payment_transfer(20,
        create_organisation.token,
        send_user=user5,
        send_transfer_account=user5.default_transfer_account,
        receive_user=user6,
        receive_transfer_account=user6.default_transfer_account,
        transfer_use=str(int(tu3.id))
    )
    p4.created = p4.created - timedelta(days=4)

    p4 = make_payment_transfer(20,
        create_organisation.token,
        send_user=user6,
        send_transfer_account=user6.default_transfer_account,
        receive_user=user5,
        receive_transfer_account=user5.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    p4.created = p4.created - timedelta(days=6)
    db.session.commit()

@pytest.mark.parametrize("metric_type, status_code", [
    ("user", 200),
    ("all", 200),
    ("credit_transfer", 200),
    ("notarealmetrictype", 500),
])
def test_get_metric_filters(test_client, complete_admin_auth_token, external_reserve_token,
                             metric_type, status_code):
    # Tests getting list of availible metrics filters from the /api/v1/metrics/filters endpoint
    response = test_client.get(
        f'/api/v1/metrics/filters/?metric_type={metric_type}',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
    )

    assert response.status_code == status_code

    if status_code == 200:
        if metric_type == 'user':
            assert response.json['data']['filters'] == USER_FILTERS
        else:
            assert response.json['data']['filters'] == ALL_FILTERS

base_participant = {
    'data':
    {'transfer_stats':
        {'active_filters': [],
        'active_group_by': 'account_type',
        'active_users': {'aggregate': {'total': 0}, 'timeseries': {}},
        'mandatory_filter': {},
        'master_wallet_balance': 0,
        'total_beneficiaries': 0,
        'total_users': 0,
        'total_vendors': 0,
        'users_created': {'aggregate': {'total': 1},
        'timeseries': {}}}},
        'message': 'Successfully Loaded.',
        'status': 'success'
}


base_all = {'data':
    {'transfer_stats':
        {'active_filters': [],
        'active_group_by': 'account_type',
        'active_users': {'aggregate': {'total': 0}, 'timeseries': {}},
        'all_payments_volume': {'aggregate': {'total': 0}, 'timeseries': {}},
        'daily_disbursement_volume': {'aggregate': {'total': 0},'timeseries': {}},
        'daily_transaction_count': {'aggregate': {'total': 0}, 'timeseries': {}},
        'daily_transaction_volume': {'aggregate': {'total': 0}, 'timeseries': {}},
        'users_who_made_purchase': {'aggregate': {'total': 0}, 'timeseries': {}},
        'exhausted_balance': 0,
        'has_transferred_count': 0,
        'mandatory_filter': {},
        'master_wallet_balance': 0,
        'total_beneficiaries': 0,
        'total_distributed': 0.0,
        'total_exchanged': 0.0,
        'total_spent': 0.0,
        'total_users': 0,
        'total_vendors': 0,
        'trades_per_user': {'aggregate': {'total': 0}, 'timeseries': {}},
        'transfer_amount_per_user': {'aggregate': {'total': 0}, 'timeseries': {}},
        'users_created': {'aggregate': {'total': 1}, 'timeseries': {}}}},
        'message': 'Successfully Loaded.',
        'status': 'success'}


base_transfer = {'data':
    {'transfer_stats':
        {'active_filters': [],
        'active_group_by': 'account_type',
        'all_payments_volume': {'aggregate': {'total': 0}, 'timeseries': {}},
        'daily_disbursement_volume': {'aggregate': {'total': 0}, 'timeseries': {}},
        'daily_transaction_count': {'aggregate': {'total': 0}, 'timeseries': {}},
        'daily_transaction_volume': {'aggregate': {'total': 0}, 'timeseries': {}},
        'users_who_made_purchase': {'aggregate': {'total': 0}, 'timeseries': {}},
        'exhausted_balance': 0,
        'has_transferred_count': 0,
        'mandatory_filter': {},
        'master_wallet_balance': 0,
        'total_distributed': 0.0,
        'total_exchanged': 0.0,
        'total_spent': 0.0,
        'trades_per_user': {'aggregate': {'total': 0}, 'timeseries': {}},
        'transfer_amount_per_user': {'aggregate': {'total': 0}, 'timeseries': {}}}},
        'message': 'Successfully Loaded.',
        'status': 'success'}


@pytest.mark.parametrize("metric_type, status_code", [
    ("user", 200),
    ("all", 200),
    ("credit_transfer", 200),
    ("notarealmetrictype", 500),
])
def test_get_zero_metrics(test_client, complete_admin_auth_token, external_reserve_token, create_organisation,
                             metric_type, status_code):
    def get_metrics(metric_type):
        return test_client.get(
            f'/api/v1/metrics/?metric_type={metric_type}&disable_cache=True&org={create_organisation.id}&group_by=account_type',
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
    elif metric_type == 'all':
        assert response.json == base_all
    elif metric_type == 'user':
        assert response.json == base_participant

@pytest.mark.parametrize("metric_type, params, status_code, requested_metric, group_by, output_file", [
    ("all", None, 200, None, 'account_type', 'all_by_account_type.json'),
    ("all", "rounded_account_balance(GT)(2)", 200, None, 'account_type', 'all_by_account_type_filtered.json'),
    ("credit_transfer", None, 200, None, 'transfer_usage', 'credit_transfer_by_transfer_usage.json'),
    ("user", None, 200, None, 'account_type', 'user_by_account_type.json'),
    ("credit_transfer", None, 200, None, 'transfer_type', 'credit_transfer_by_transfer_type.json'),
    ("all", None, 200, 'active_users', 'account_type', 'requested_metric_active_users.json'),
    ("all", None, 500, None, 'transfer_usage', ''), # 500 because can't group all by transfer_usage 
    ("user", None, 500, None, 'transfer_usage', ''), # 500 because can't group user by transfer_usage
    ("user", 'transfer_amount(LT)(50)', 500, None, 'account_type', ''), # 500 because can't filter user by transfer_amount
    ("all", 'transfer_amount(LT)(50)', 500, None, 'account_type', ''), # 500 because can't filter all by transfer_amount
    ("notarealmetrictype", None, 500, None, 'transfer_usage', ''),
])
def test_get_summed_metrics(
        test_client, complete_admin_auth_token, external_reserve_token, create_organisation, generate_timeseries_metrics,
        metric_type, params, status_code, requested_metric, group_by, output_file
):
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
                assert returned_stats[do]['aggregate'] == desired_output[do]['aggregate']
                for timeseries_category in returned_stats[do]['timeseries']:
                    for idx in range(len(returned_stats[do]['timeseries'][timeseries_category])):
                        assert returned_stats[do]['timeseries'][timeseries_category][idx]['value'] == desired_output[do]['timeseries'][timeseries_category][idx]['value']
