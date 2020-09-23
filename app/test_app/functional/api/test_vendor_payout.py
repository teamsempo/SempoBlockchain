import json, pytest, config, base64
from server.utils.auth import get_complete_auth_token
from server.utils.transfer_enums import TransferTypeEnum, TransferStatusEnum
from server import db
import csv
from io import StringIO

def test_get_vendor_payout(test_client, authed_sempo_admin_user, create_transfer_account_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)

    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(500000)
    db.session.commit()

    response = test_client.post(
        f"/api/v1/get_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        data=json.dumps(dict({}))
    )
    resp = response.data.decode('ascii')

    f = StringIO(resp)
    reader = csv.reader(f)
    formatted_results = list(reader)
    formatted_results[1][3] = 'SOME DATE'
    assert formatted_results == [
        [
            'ID', 
            'First Name', 
            'Last Name', 
            'Created', 
            'Current Balance', 
            'Total Sent', 
            'Total Received', 
            'Approved', 
            'Beneficiary', 
            'Vendor', 
            'Transaction ID', 
            'Amount Due Today', 
            'Payment Has Been Made', 
            'Bank Payment Date'
        ], [
            '4', 
            'Transfer', 
            'User', 
            'SOME DATE', 
            '500000.0', 
            '500000.000000000000', 
            '0', 
            'False', 
            'False', 
            'True', 
            '1', 
            '500000.0', 
            '', 
            ''
        ]
    ]
    transfer = user.transfer_account.credit_sends[0]
    assert transfer.transfer_type == TransferTypeEnum.PAYMENT
    assert transfer.sender_transfer_account == user.transfer_account
    assert transfer.recipient_transfer_account == user.transfer_account.token.float_account
    assert transfer.transfer_status == TransferStatusEnum.PENDING

def test_process_vendor_payout_pend(test_client, authed_sempo_admin_user, create_transfer_account_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(500000)
    user.transfer_account.is_approved=True
    user.transfer_account.token.float_account.is_approved=True
    db.session.commit()

    test_client.post(
        f"/api/v1/process_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        json={
            'csv_data':  """ID,First Name,Last Name,Created,Current Balance,Total Sent,Total Received,Approved,Beneficiary,Vendor,Transaction ID,Amount Due Today,Payment Has Been Made,Bank Payment Date\n4,Transfer,User,SOME DATE,500000.0,500000.000000000000,0,True,False,True,1,500000.0,,09/30/2020"""
        }
    )
    transfer = user.transfer_account.credit_sends[0]

    assert transfer.transfer_status == TransferStatusEnum.PENDING

def test_process_vendor_payout_reject(test_client, authed_sempo_admin_user, create_transfer_account_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(500000)
    user.transfer_account.is_approved=True
    db.session.commit()

    test_client.post(
        f"/api/v1/process_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        json={
            'csv_data':  """ID,First Name,Last Name,Created,Current Balance,Total Sent,Total Received,Approved,Beneficiary,Vendor,Transaction ID,Amount Due Today,Payment Has Been Made,Bank Payment Date\n4,Transfer,User,SOME DATE,500000.0,500000.000000000000,0,True,False,True,1,500000.0,FALSE,09/30/2020"""
        }
    )
    transfer = user.transfer_account.credit_sends[0]
    assert transfer.transfer_status == TransferStatusEnum.REJECTED
