import pytest
from server.models.transfer_usage import TransferUsage
from server.utils.transfer_filter import ALL_FILTERS, USER_FILTERS
from server.utils.credit_transfer import make_payment_transfer
from server.utils.user import create_transfer_account_user
from server import db
import json

@pytest.fixture(scope='module')
def generate_metrics(create_organisation):
    # Does a bunch of things which generate metrics, and sums them at the same time
    # Results in the following metrics:
    # disbursement_volume: 300
    # transaction_volume: 150
    # exhausted_balance: 1
    # has_transferred_count: 2
    # last_day_volume: 150
    # total_spent: 150
    # total_beneficiaries: 1

    user1 = create_transfer_account_user(first_name='Paul',
                                    last_name='Buffano',
                                    phone="+19025551234",
                                    organisation=create_organisation,
                                    is_beneficiary=True)
    user1.default_transfer_account.is_approved = True

    user1.default_transfer_account._make_initial_disbursement(100, True)

    user2 = create_transfer_account_user(first_name='Roy',
                                    last_name='Donk',
                                    phone="+19025551235",
                                    organisation=create_organisation)
    user2.default_transfer_account.is_approved = True

    user2.default_transfer_account._make_initial_disbursement(200, True)

    db.session.commit()

    tu1 = TransferUsage.find_or_create("Pizza")
    tu2 = TransferUsage.find_or_create("HotDog")
    tu3 = TransferUsage.find_or_create("Burger")
    make_payment_transfer(100,
        create_organisation.token,
        send_user=user1,
        send_transfer_account=user1.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    make_payment_transfer(25,
        create_organisation.token,
        send_user=user2,
        send_transfer_account=user2.default_transfer_account,
        receive_user=user1,
        receive_transfer_account=user1.default_transfer_account,
        transfer_use=str(int(tu1.id))
    )
    make_payment_transfer(5,
        create_organisation.token,
        send_user=user1,
        send_transfer_account=user1.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu2.id))
    )
    make_payment_transfer(20,
        create_organisation.token,
        send_user=user1,
        send_transfer_account=user1.default_transfer_account,
        receive_user=user2,
        receive_transfer_account=user2.default_transfer_account,
        transfer_use=str(int(tu3.id))
    )

@pytest.mark.parametrize("metric_type, status_code", [
    ("user", 200),
    ("all", 200),
    ("transfer", 200),
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
            assert response.json['data']['filters'] == json.dumps(USER_FILTERS)
        else:
            assert response.json['data']['filters'] == json.dumps(ALL_FILTERS)

base_participant = {'data': 
    {'transfer_stats': 
        {'total_beneficiaries': 0, 
        'total_users': 0, 
        'total_vendors': 0,
        'master_wallet_balance': 0,
        'users_created': {'aggregate': {'total': 0}, 'timeseries': []}
        }
    }, 
    'message': 'Successfully Loaded.', 'status': 'success'
}

base_all = {'data':
    {'transfer_stats': 
        {
        'total_beneficiaries': 0, 
        'total_users': 0, 
        'total_vendors': 0,
        'master_wallet_balance': 0,
        'users_created': {'aggregate': {'total': 0}, 'timeseries': []},
        'daily_disbursement_volume': [], 
        'daily_transaction_volume': [], 
        'exhausted_balance': 0, 
        'has_transferred_count': 0, 
        'master_wallet_balance': 0, 
        'total_distributed': 0.0, 
        'total_exchanged': 0.0, 
        'total_spent': 0.0, 
        'transfer_use_breakdown': [],
        'trades_per_user': {'aggregate': {'total': 0}, 'timeseries': []}, 
        'transfer_amount_per_user': {'aggregate': {'total': 0}, 'timeseries': []}, 
        'daily_transaction_count': {'aggregate': {'total': 0}, 'timeseries': []},
        }
    },
    'message': 'Successfully Loaded.',
    'status': 'success'
}

base_transfer = {'data': 
    {'transfer_stats': 
        {'daily_disbursement_volume': [], 
        'daily_transaction_volume': [], 
        'exhausted_balance': 0, 
        'has_transferred_count': 0, 
        'master_wallet_balance': 0, 
        'total_distributed': 0.0, 
        'total_exchanged': 0.0, 
        'total_spent': 0.0, 
        'transfer_use_breakdown': [],
        'trades_per_user': {'aggregate': {'total': 0}, 'timeseries': []}, 
        'transfer_amount_per_user': {'aggregate': {'total': 0}, 'timeseries': []}, 
        'daily_transaction_count': {'aggregate': {'total': 0}, 'timeseries': []},
        }
    },
    'message': 'Successfully Loaded.',
    'status': 'success'
}

@pytest.mark.parametrize("metric_type, status_code", [
    ("user", 200),
    ("all", 200),
    ("transfer", 200),
    ("notarealmetrictype", 500),
])
def test_get_zero_metrics(test_client, complete_admin_auth_token, external_reserve_token, create_organisation,
                             metric_type, status_code):
    def get_metrics(metric_type):
        return test_client.get(
            f'/api/v1/metrics/?metric_type={metric_type}&disable_cache=True&org={create_organisation.id}',
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
    if metric_type == 'transfer':
        assert response.json == base_transfer
    elif metric_type == 'all':
        assert response.json == base_all
    elif metric_type == 'user':
        assert response.json == base_participant

@pytest.mark.parametrize("metric_type, status_code", [
    ("all", 200),
    ("user", 200),
    ("transfer", 200),
    ("notarealmetrictype", 500),
])
def test_get_summed_metrics(test_client, complete_admin_auth_token, external_reserve_token, create_organisation, generate_metrics,
                             metric_type, status_code):
    def get_metrics(metric_type):
        return test_client.get(
            f'/api/v1/metrics/?metric_type={metric_type}&disable_cache=True&org={create_organisation.id}',
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

    if metric_type == 'transfer' or metric_type == 'all':
        assert returned_stats['daily_disbursement_volume'][0]['volume'] == 300
        assert returned_stats['daily_transaction_volume'][0]['volume'] == 150
        assert returned_stats['exhausted_balance'] == 0
        assert returned_stats['has_transferred_count'] == 2
        assert returned_stats['total_distributed'] == 300
        assert returned_stats['total_exchanged'] == 0
        assert returned_stats['total_spent'] == 150
        assert returned_stats['transfer_use_breakdown'] == [[['Burger'], 1], [['HotDog'], 1], [['Pizza'], 2]]
    elif metric_type == 'participant' or metric_type == 'all':
        assert returned_stats['total_beneficiaries'] == 1
        assert returned_stats['total_users'] == 1
        assert returned_stats['total_vendors'] == 0
