from flask import Blueprint, request, send_file
from flask.views import MethodView
from flask import g

from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.utils.credit_transfer import make_withdrawal_transfer
from server.utils.transfer_enums import TransferModeEnum
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
        if post_data:
            account_ids = post_data.get('accounts', [])

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
            'ID', 
            'ContactName', 
            'Current Balance', 
            'Total Sent', 
            'Total Received',
            'Approved', 
            'Beneficiary', 
            'Vendor',
            'InvoiceDate',
            'DueDate',
            'Transaction ID',
            'UnitAmount',
            'Payment Has Been Made',
            'Bank Payment Date',
        ])
        for v in vendors:
            transfer = make_withdrawal_transfer(
                Decimal(v._balance_wei or 0) / Decimal(1e16),
                token=v.token,
                send_user=v.primary_user,
                sender_transfer_account=v,
                transfer_mode=TransferModeEnum.INTERNAL,
                require_sender_approved=False,
                automatically_resolve_complete=False,
            )

            db.session.flush()
            
            writer.writerow([
                v.id,
                v.primary_user.first_name + '  ' + v.primary_user.last_name,
                v.balance,
                v.total_sent,
                v.total_received,
                v.is_approved,
                v.primary_user.has_beneficiary_role,
                v.primary_user.has_vendor_role,
                datetime.today().strftime('%Y-%m-%d'),
                (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
                transfer.id,
                v.balance,
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
            vendor = db.session.query(TransferAccount).filter(TransferAccount.id == line['ID']).first()
            if not vendor.primary_user.has_vendor_role:
                raise Exception(f'{vendor} is not a vendor!')
            transfer = db.session.query(CreditTransfer).filter(CreditTransfer.id == line['Transaction ID']).first()
            if not transfer:
                raise Exception(f'Tranfer with ID {line["Transaction ID"]} not found!')
            if float(transfer.transfer_amount) != float(line["UnitAmount"]):
                raise Exception(f'Invalid transfer amount!')
            if line['Payment Has Been Made'].upper() == 'TRUE' and line['Bank Payment Date']:
                try:
                    transfer.resolve_as_complete_and_trigger_blockchain()
                except:
                    pass
            elif line['Payment Has Been Made'] == 'FALSE':
                transfer.resolve_as_rejected()
            transfers.append(transfer)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID', 
            'First Name', 
            'Last Name', 
            'Transfer Created',
            'Transfer Type',
            'Transfer Amount',
            'Transfer Status',
        ])
        for t in transfers:
            writer.writerow([
                t.sender_transfer_account.id,
                t.sender_transfer_account.primary_user.first_name,
                t.sender_transfer_account.primary_user.last_name,
                t.created,
                t.transfer_type.value,
                t.transfer_amount,
                t.transfer_status.value
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
