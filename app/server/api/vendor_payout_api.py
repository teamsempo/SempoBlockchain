from flask import Blueprint, request, send_file, make_response, jsonify
from flask.views import MethodView
from flask import g

from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.utils.credit_transfer import make_withdrawal_transfer
from server.utils.transfer_enums import TransferModeEnum, TransferStatusEnum, TransferTypeEnum
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

        payout_withdrawal_limit = g.active_organisation._minimum_vendor_payout_withdrawal_wei
        if not isinstance(account_ids, list):
            response_object = {
                'message': 'Accounts parameter expects a list',
            }
            return make_response(jsonify(response_object)), 400

        if account_ids:
            vendors = db.session.query(TransferAccount)\
                .filter(TransferAccount.account_type == TransferAccountType.USER)\
                .filter(TransferAccount.id.in_(account_ids))\
                .all()

            for vendor in vendors:
                if not vendor.primary_user.has_vendor_role:

                    response_object = {
                        'message': f'Transfer account with id {vendor.id} not a vendor account. Please only IDs of vendor accounts',
                    }
                    return make_response(jsonify(response_object)), 400

            selected_vendor_ids = [v.id for v in vendors]
            list_difference = [item for item in account_ids if item not in selected_vendor_ids]
            if list_difference:
                response_object = {
                    'message': f'Accounts {list_difference} were requested but do not exist',
                }
                return make_response(jsonify(response_object)), 400
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
            print('RRR')
            print(withdrawal_amount)
            print(v._balance_wei)
            print(payout_withdrawal_limit)
            
            print(v)
            print(v.primary_user)
            print(v)

            if withdrawal_amount > 0 and (v._balance_wei or 0) >= payout_withdrawal_limit:
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
                    f'{v.primary_user.first_name or ""} {v.primary_user.last_name or ""}',
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
                response_object = {
                    'message': 'Please provide a CSV file'
                }
                return make_response(jsonify(response_object)), 400

            csv_data = post_data.get('csv_data', [])
            f = io.StringIO(csv_data)
            reader = csv.DictReader(f)

        transfers = []
        for line in reader:
            tid = line['Transfer ID']
            transfer = db.session.query(CreditTransfer).filter(CreditTransfer.id == tid).first()
            message = ''

            if not transfer:
                message = f'Transfer with ID {tid} not found!'
                transfers.append((tid, None, message))
                continue

            if transfer.transfer_type != TransferTypeEnum.WITHDRAWAL:
                message = f'Not a withdrawal!'
                transfers.append((tid, None, message))
                continue

            got_amount = round(dollars_to_cents(line["UnitAmount"]))
            expected_amount = round(transfer.transfer_amount)
            if got_amount != expected_amount:
                message = f'Transfer Amounts do not match (got {cents_to_dollars(got_amount)}, expected {cents_to_dollars(expected_amount)})!'
                transfers.append((tid, None, message))
                continue

            try:
                if line['Payment Has Been Made'].upper() == 'TRUE' and line['Bank Payment Date']:
                    transfer.resolve_as_complete_and_trigger_blockchain()
                    message = 'Transfer Success'
                elif line['Payment Has Been Made'] == 'FALSE':
                    transfer.resolve_as_rejected()
                    message = 'Transfer Rejected'
            except Exception as e:
                message = str(e)

            transfers.append((tid, transfer, message))

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Transfer ID',
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
        for tid, t, m in transfers:
            writer.writerow([
                tid,
                t and t.sender_transfer_account.id,
                t and t.sender_transfer_account.primary_user.phone,
                t and t.sender_transfer_account.primary_user.first_name,
                t and t.sender_transfer_account.primary_user.last_name,
                t and t.created,
                t and t.transfer_type.value,
                t and cents_to_dollars(t.transfer_amount),
                t and t.transfer_status.value,
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
