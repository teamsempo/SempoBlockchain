from flask import Blueprint, request, send_file
from flask.views import MethodView
from flask import g

from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.utils.credit_transfer import make_withdrawal_transfer
from server.utils.transfer_enums import TransferModeEnum, TransferStatusEnum
from server.utils.credit_transfer import cents_to_dollars, dollars_to_cents
from server.utils.auth import requires_auth
from server import db

import json
import csv
import io
import codecs
from decimal import Decimal
from datetime import datetime, timedelta

vendor_payout = Blueprint('vendor_payout', __name__)

class VendorPayoutAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        # Process post data
        post_data = request.get_json()
        account_ids = []
        relist_existing = True
        if post_data:
            account_ids = post_data.get('accounts', [])
            relist_existing = post_data.get('relist_existing', True)

        if not isinstance(account_ids, list):
            raise Exception('accounts parameter expects a list')
        if account_ids:
            vendors = db.session.query(TransferAccount).filter(TransferAccount.account_type != TransferAccountType.FLOAT).filter(TransferAccount.id.in_(account_ids)).all()
            for vendor in vendors:
                if not vendor.primary_user.has_vendor_role:
                    raise Exception(f'Transfer account with id {vendor.id} not a vendor account. Please only IDs of vendor accounts')

            selected_vendor_ids = [v.id for v in vendors]
            list_difference = [item for item in account_ids if item not in selected_vendor_ids]
            if list_difference:
                raise Exception(f'Accounts {list_difference} were requested but do not exist')
        else:
            vendor_users = db.session.query(User)\
                .filter(User.has_vendor_role)\
                .all()
            vendors = [v.default_transfer_account for v in vendor_users]
            vendors = filter(lambda vendor: not vendor.is_ghost, vendors)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
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
            'Bank Payment Date',
        ])
        for v in vendors:
            if relist_existing:
                withdrawals = (CreditTransfer.query
                               .filter(CreditTransfer.sender_transfer_account_id == v.id)
                               .filter(CreditTransfer.transfer_status == TransferStatusEnum.PENDING).all())
            else:
                withdrawals = []

            withdrawal_amount = Decimal(v._balance_wei or 0) / Decimal(1e16)
            if withdrawal_amount > 0:

                transfer = make_withdrawal_transfer(
                    withdrawal_amount,
                    token=v.token,
                    send_user=v.primary_user,
                    sender_transfer_account=v,
                    transfer_mode=TransferModeEnum.INTERNAL,
                    require_sender_approved=False,
                    automatically_resolve_complete=False,
                )

                db.session.flush()

                withdrawals.append(transfer)

            for w in withdrawals:
                writer.writerow([
                    v.id,
                    v.primary_user.phone,
                    v.primary_user.first_name + ' ' + v.primary_user.last_name,
                    cents_to_dollars(v.balance),
                    cents_to_dollars(v.total_sent),
                    cents_to_dollars(v.total_received),
                    v.is_approved,
                    v.primary_user.has_beneficiary_role,
                    v.primary_user.has_vendor_role,
                    datetime.today().strftime('%Y-%m-%d'),
                    (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    w.id,
                    cents_to_dollars(w.transfer_amount),
                    '',
                    '',
                ])


        # Encode the CSV such that it can be sent as a file
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        return send_file(bytes_output, as_attachment=True, attachment_filename='vendor_payout.csv', mimetype='text/csv')

class ProcessVendorPayout(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        # Handle a file upload, or CSV in JSON
        if request.files:
            flask_file = request.files['file']
            stream = codecs.iterdecode(flask_file.stream, 'utf-8')
            reader = csv.DictReader(stream)
        else:
            post_data = request.get_json()
            if not post_data:
                raise Exception('Please provide a CSV file')
            csv_data = post_data.get('csv_data', [])
            f = io.StringIO(csv_data)
            reader = csv.DictReader(f)
        transfers = []
        for line in reader:
            transfer = db.session.query(CreditTransfer).filter(CreditTransfer.id == line['Transaction ID']).first()
            message = ''
            if not transfer:
                raise Exception(f'Transfer with ID {line["Transfer ID"]} not found!')
            if round(transfer.transfer_amount) != round(dollars_to_cents(line["UnitAmount"])):
                raise Exception(f'Invalid transfer amount!')
            if line['Payment Has Been Made'].upper() == 'TRUE' and line['Bank Payment Date']:
                try:
                    transfer.resolve_as_complete_and_trigger_blockchain()
                    message = 'Transfer Success'
                except Exception as e:
                    message = str(e)
            elif line['Payment Has Been Made'] == 'FALSE':
                transfer.resolve_as_rejected()
                message = 'Transfer Rejected'
            transfers.append((transfer, message))

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Vendor Account ID',
            'Phone',
            'First Name', 
            'Last Name', 
            'Transfer Created',
            'Transfer Type',
            'Transfer Amount',
            'Transfer Status',
            'Message'
        ])
        for t, m in transfers:
            writer.writerow([
                t.sender_transfer_account.id,
                t.sender_transfer_account.primary_user.phone,
                t.sender_transfer_account.primary_user.first_name,
                t.sender_transfer_account.primary_user.last_name,
                t.created,
                t.transfer_type.value,
                cents_to_dollars(t.transfer_amount),
                t.transfer_status.value,
                m
            ])
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        return send_file(bytes_output, as_attachment=True, attachment_filename='vendor_payout.csv', mimetype='text/csv')


# Semi-counter intuitive, but something which "gets" is posting because of the side effects
vendor_payout.add_url_rule(
    '/get_vendor_payout/',
    view_func=VendorPayoutAPI.as_view('get_vendor_payout'),
    methods=['POST']
)

vendor_payout.add_url_rule(
    '/process_vendor_payout/',
    view_func=ProcessVendorPayout.as_view('process_vendor_payout'),
    methods=['POST']
)
