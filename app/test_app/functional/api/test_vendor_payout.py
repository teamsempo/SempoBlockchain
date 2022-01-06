import json, pytest, config, base64
from server.utils.auth import get_complete_auth_token
from server.utils.transfer_enums import TransferTypeEnum, TransferStatusEnum
from server import db
from server.models.kyc_application import KycApplication
import csv
from io import StringIO
from sqlalchemy.orm.attributes import flag_modified

def test_get_vendor_payout_with_withdrawal_limit(test_client, authed_sempo_admin_user, create_transfer_account_user):
    authed_sempo_admin_user.organisations[0].minimum_vendor_payout_withdrawal = 200
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(100)
    user.is_phone_verified = True
    kyc = KycApplication(type='INDIVIDUAL')
    user.kyc_applications = [kyc]
    user.kyc_applications[0].kyc_status = 'VERIFIED'
    db.session.commit()

    response = test_client.post(
        f"/api/v1/get_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        data=json.dumps(dict({}))
    )
    assert len(user.transfer_account.credit_sends) == 0

def test_get_vendor_payout(test_client, authed_sempo_admin_user, create_transfer_account_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(1000)
    user.is_phone_verified = True
    kyc = KycApplication(type='INDIVIDUAL')
    user.kyc_applications = [kyc]
    user.kyc_applications[0].kyc_status = 'VERIFIED'
    user.phone = '+19025551234'
    flag_modified(user, '_held_roles')
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
    formatted_results[1][9] = 'SOME DATE'
    formatted_results[1][10] = 'SOME DATE'
    assert formatted_results == [
        [
            'Vendor Account ID',
            'Phone',
            'ContactName', 
            'Current Balance', 
            'Total Sent', 
            'Total Received', 
            'Approved', 
            'Beneficiary', 
            'Vendor', 
            'InvoiceDate', 
            'DueDate', 
            'Transfer ID',
            'UnitAmount', 
            'Payment Has Been Made', 
            'Bank Payment Date'
        ], [
            '4',
            user.phone,
            'Transfer User',
            '0',
            '10', 
            '0', 
            'True', 
            'False', 
            'True', 
            'SOME DATE', 
            'SOME DATE', 
            '1', 
            '10', 
            '', 
            ''
        ]
    ]    
    transfer = user.transfer_account.credit_sends[0]
    assert transfer.transfer_type == TransferTypeEnum.WITHDRAWAL
    assert transfer.sender_transfer_account == user.transfer_account
    assert transfer.recipient_transfer_account == user.transfer_account.token.float_account
    assert transfer.transfer_status == TransferStatusEnum.PENDING

def test_process_vendor_payout_approve(test_client, authed_sempo_admin_user, create_transfer_account_user, mock_sms_apis):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(1000)
    user.transfer_account.is_approved=True
    user.is_phone_verified = True
    user.phone = '+19025551234'
    user.kyc_applications[0].kyc_status = 'VERIFIED'

    db.session.commit()

    test_client.post(
        f"/api/v1/process_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        json={
            'csv_data': f"""ID,Phone,First Name,Last Name,Created,Current Balance,Total Sent,Total Received,Approved,Beneficiary,Vendor,Transfer ID,UnitAmount,Payment Has Been Made,Bank Payment Date\n4,{user.phone},Transfer,User,SOME DATE,10.0,10.000000000000,0,True,False,True,1,10.0,TRUE,09/30/2020"""
        }
    )
    messages = mock_sms_apis
    transfer = user.transfer_account.credit_sends[0]
    assert transfer.transfer_status == TransferStatusEnum.COMPLETE
    assert messages[0] == {'phone': '+19025551234', 'message': 'Hello Transfer, a total of 10 AUD has been deposited into your account.'}
    transfer.transfer_status = TransferStatusEnum.PENDING

def test_process_vendor_payout_reject(test_client, authed_sempo_admin_user, create_transfer_account_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(1000)
    user.transfer_account.is_approved=True
    user.is_phone_verified = True
    user.kyc_applications[0].kyc_status = 'VERIFIED'

    db.session.commit()

    test_client.post(
        f"/api/v1/process_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        json={
            'csv_data': f"""ID,Phone,First Name,Last Name,Created,Current Balance,Total Sent,Total Received,Approved,Beneficiary,Vendor,Transfer ID,UnitAmount,Payment Has Been Made,Bank Payment Date\n4,{user.phone},Transfer,User,SOME DATE,10.0,10.000000000000,0,True,False,True,1,10.0,FALSE,09/30/2020"""
        }
    )
    transfer = user.transfer_account.credit_sends[0]
    assert transfer.transfer_status == TransferStatusEnum.REJECTED
    transfer.transfer_status = TransferStatusEnum.PENDING


def test_process_vendor_payout_pending(test_client, authed_sempo_admin_user, create_transfer_account_user):
    auth = get_complete_auth_token(authed_sempo_admin_user)
    user = create_transfer_account_user
    user.transfer_account.is_vendor = True
    user.set_held_role('VENDOR', 'supervendor')
    user.transfer_account.approve_and_disburse()
    user.transfer_account.organisation = authed_sempo_admin_user.organisations[0]
    user.transfer_account.set_balance_offset(1000)
    user.transfer_account.is_approved=True
    user.is_phone_verified = True
    user.phone = '+19025551234'
    user.kyc_applications[0].kyc_status = 'VERIFIED'

    db.session.commit()

    test_client.post(
        f"/api/v1/process_vendor_payout/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        json={
            'csv_data': f"""ID,Phone,First Name,Last Name,Created,Current Balance,Total Sent,Total Received,Approved,Beneficiary,Vendor,Transaction ID,UnitAmount,Payment Has Been Made,Bank Payment Date\n4,{user.phone},Transfer,User,SOME DATE,10.0,10.000000000000,0,True,False,True,1,10.0,,09/30/2020"""
        }
    )
    transfer = user.transfer_account.credit_sends[0]

    assert transfer.transfer_status == TransferStatusEnum.PENDING
    transfer.transfer_status = TransferStatusEnum.PENDING
