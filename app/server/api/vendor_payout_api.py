from flask import Blueprint, request, send_file
from flask.views import MethodView
from flask import g

from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.credit_transfer import CreditTransfer
from server.utils.credit_transfer import make_payment_transfer
from server.utils.transfer_enums import TransferModeEnum
from server.utils.auth import requires_auth
from server import db

import json
import csv
import io
import codecs
from decimal import Decimal

vendor_payout = Blueprint('vendor_payout', __name__)

class GetVendorPayoutAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        # Process post data
        post_data = request.get_json()
        account_ids = post_data.get('accounts', [])

        if not isinstance(account_ids, list):
            raise Exception('accounts parameter expects a list')
        if account_ids:
            vendors = db.session.query(TransferAccount).filter(TransferAccount.id.in_(account_ids)).all()
            for vendor in vendors:
                if not vendor.is_vendor:
                    raise Exception(f'Transfer account with id {vendor.id} not a vendor account. Please only IDs of vendor accounts')

            selected_vendor_ids = [v.id for v in vendors]
            list_difference = [item for item in account_ids if item not in selected_vendor_ids]
            if list_difference:
                raise Exception(f'Accounts {list_difference} were requested but do not exist')
        else:
            vendors = db.session.query(TransferAccount).filter(TransferAccount.is_vendor == True).all()

        # Get float wallet
        float_wallet = TransferAccount.query.execution_options(show_all=True).filter(
            TransferAccount.account_type == TransferAccountType.FLOAT
        ).first()
        if not float_wallet:
            raise Exception(f'Float wallet does not exist')

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
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
            'Bank Payment Date',
        ])

        for v in vendors:
            # Cash out vendors to float wallet
            # NOTE: MAJOR WARNING! DONT MERGE THIS YET!
            # Sending from the transfer account back to itself. This is just abecause the float account
            # does not have an attached token and I'm not sure what we're going to do with that yet
            v.is_approved = True
            transfer = make_payment_transfer(
                Decimal(v._balance_wei or 0) / Decimal(1e16),
                token=float_wallet.token,
                send_user=v.primary_user,
                send_transfer_account=v,
                receive_transfer_account=v,
                transfer_mode=TransferModeEnum.INTERNAL,
                automatically_resolve_complete=False,
                require_sender_approved=False,
                require_recipient_approved=False
            )

            writer.writerow([
                v.id,
                v.primary_user.first_name,
                v.primary_user.last_name,
                v.created,
                v.balance,
                v.total_sent,
                v.total_received,
                v.is_approved,
                v.is_beneficiary,
                v.is_vendor,
                transfer.id,
                v.balance,
                '',
                '',
            ])

        # Encode the CSV such that it can be sent as a file
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8'))
        # seeking was necessary. Python 3.5.2, Flask 0.12.2
        bytes_output.seek(0)
        return send_file(bytes_output, as_attachment=True, attachment_filename='vendor_payout.csv', mimetype='text/csv')

class ProcessVendorPayout(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        flask_file = request.files['file']
        if not flask_file:
            raise Exception('Please provide a CSV file')

        data = []
        stream = codecs.iterdecode(flask_file.stream, 'utf-8')
        reader = csv.DictReader(stream)

        for line in reader:
            vendor = db.session.query(TransferAccount).filter(TransferAccount.id == line['ID']).first()
            if not vendor.is_vendor:
                raise Exception(f'{vendor} is not a vendor!')
            transfer = db.session.query(CreditTransfer).filter(CreditTransfer.id == line['Transaction ID']).first()
            if not transfer:
                raise Exception(f'Tranfer with ID {line["Transaction ID"]} not found!')
            if float(transfer.transfer_amount) != float(line["Amount Due Today"]):
                raise Exception(f'Invalid transfer amount!')
        #f = request.files['file']
        #csv_file = f.read()
        #a = csv.DictReader(csv_file.splitlines(), skipinitialspace=True)
        #print(a)  
        #for line in a:
        #    print(a)
        return "ayy"

# Semi-counter intuitive, but something which "gets" is posting because of the side effects
vendor_payout.add_url_rule(
    '/get_vendor_payout/',
    view_func=GetVendorPayoutAPI.as_view('get_vendor_payout'),
    methods=['POST']
)

vendor_payout.add_url_rule(
    '/process_vendor_payout/',
    view_func=ProcessVendorPayout.as_view('process_vendor_payout'),
    methods=['POST']
)