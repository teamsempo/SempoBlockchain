from flask import Blueprint, request, make_response, jsonify, g, current_app
from flask.views import MethodView
from pyexcelerate import Workbook
from datetime import datetime, timedelta
import random, string
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import joinedload

from server import db
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.utils.auth import requires_auth
from server.utils.export import generate_pdf_export, export_workbook_via_s3, partition_query
from server.utils.executor import standard_executor_job, add_after_request_executor_job
from server.utils.transfer_filter import process_transfer_filters
from server.utils.search import generate_search_query

export_blueprint = Blueprint('export', __name__)

@standard_executor_job
def generate_export(post_data):
    from server.models.credit_transfer import CreditTransfer
    from server.models.transfer_account import TransferAccount
    from server.models.user import User

    export_type = post_data.get('export_type')
    include_transfers = post_data.get('include_transfers')  # True or False
    include_sent_and_received = post_data.get('include_sent_and_received')  # True or False
    include_custom_attributes = post_data.get('include_custom_attributes')  # True or False
    user_type = post_data.get('user_type')  # Beneficiaries, Vendors, All

    transfer_account_columns = [
        {'header': 'Account ID',            'query_type': 'db',     'query': 'id'},
        {'header': 'User ID',               'query_type': 'custom', 'query': 'user_id'},
        {'header': 'First Name',            'query_type': 'custom', 'query': 'first_name'},
        {'header': 'Last Name',             'query_type': 'custom', 'query': 'last_name'},
        {'header': 'Public Serial Number',  'query_type': 'custom', 'query': 'public_serial_number'},
        {'header': 'Phone',                 'query_type': 'custom', 'query': 'phone'},
        {'header': 'Created (UTC)',         'query_type': 'db',     'query': 'created'},
        {'header': 'Approved',              'query_type': 'db',     'query': 'is_approved'},
        {'header': 'Beneficiary',           'query_type': 'custom', 'query': 'has_beneficiary_role'},
        {'header': 'Vendor',                'query_type': 'custom', 'query': 'has_vendor_role'},
        {'header': 'Location',              'query_type': 'custom', 'query': 'location'},
        {'header': 'Current Balance',       'query_type': 'custom', 'query': 'balance'},
        {'header': 'Amount Received',       'query_type': 'custom', 'query': 'received'},
        {'header': 'Amount Sent',           'query_type': 'custom', 'query': 'sent'}
    ]

    credit_transfer_columns = [
        {'header': 'ID',                'query_type': 'db',     'query': 'id'},
        {'header': 'Transfer Amount',   'query_type': 'custom', 'query': 'transfer_amount'},
        {'header': 'Created',           'query_type': 'db',     'query': 'created'},
        {'header': 'Resolved Date',     'query_type': 'db',     'query': 'resolved_date'},
        {'header': 'Transfer Type',     'query_type': 'enum',   'query': 'transfer_type'},
        {'header': 'Transfer Type',     'query_type': 'enum', 'query': 'transfer_subtype'},
        {'header': 'Transfer Status',   'query_type': 'enum',   'query': 'transfer_status'},
        {'header': 'Sender ID',         'query_type': 'db',     'query': 'sender_transfer_account_id'},
        {'header': 'Recipient ID',      'query_type': 'db',     'query': 'recipient_transfer_account_id'},
        {'header': 'Transfer Uses',     'query_type': 'custom', 'query': 'transfer_usages'},
    ]

    # need to add Balance (Payable)

    random_string = ''.join(random.choices(string.ascii_letters, k=5))
    # TODO MAKE THIS API AUTHED
    time = str(datetime.utcnow())

    base_filename = current_app.config['DEPLOYMENT_NAME'] + '-id' + str(g.user.id) + '-' + str(time[0:10]) + '-' + random_string
    workbook_filename = base_filename + '.xlsx'
    # e.g. dev-id1-2018-09-19-asfi.xlsx
    pdf_filename = base_filename + '.pdf'

    wb = Workbook()
    ws = wb.new_sheet("transfer_accounts")

    # ws1 = wb.create_sheet(title='transfer_accounts')

    user_filter = None

    for index, column in enumerate(transfer_account_columns):
        ws[1][index+1] = column['header']


    # Create transfer_accounts workbook headers
    for index, column in enumerate(transfer_account_columns):
        ws[1][index+1] = column['header']

    user_accounts = []
    credit_transfer_list = []

    # filter user accounts
    if user_type == 'beneficiary':
        user_filter = User.has_beneficiary_role

    if user_type == 'vendor':
        user_filter = User.has_vendor_role

    if user_filter is not None:
        user_accounts = User.query.filter(
            user_filter==True
        ).options(
            joinedload(User.transfer_accounts)
        )

    elif user_type == 'selected' or user_type == 'all':
        # HANDLE PARAM : search_string - Any search string. An empty string (or None) will just return everything!
        search_string = post_data.get('search_string') or ''
        # HANDLE PARAM : params - Standard filter object. Exact same as the ones Metrics uses!
        encoded_filters = post_data.get('params')
        filters = process_transfer_filters(encoded_filters)
        # HANDLE PARAM : include_accounts - Explicitly include these users
        include_accounts = post_data.get('include_accounts', [])
        # HANDLE PARAM : include_accounts - Explicitly exclude these users
        exclude_accounts = post_data.get('exclude_accounts', [])

        if include_accounts:
            transfer_accounts = db.session.query(TransferAccount).options().filter(TransferAccount.id.in_(include_accounts))
        else:
            search_query = generate_search_query(search_string, filters, order=desc, sort_by_arg='rank', include_user=True).options(
                joinedload(User.transfer_accounts)
            )

            search_query = search_query.filter(TransferAccount.id.notin_(exclude_accounts))
            transfer_accounts = [r[0] for r in search_query] # Get TransferAccount (TransferAccount, searchRank, User)
        user_accounts = [ta.primary_user for ta in transfer_accounts]

    if export_type == 'pdf':
        file_url = generate_pdf_export(user_accounts, pdf_filename)
        response_object = {
            'message': 'Export file created.',
            'data': {
                'file_url': file_url,
            }
        }

        return make_response(jsonify(response_object)), 201

    if user_accounts is not None:
        custom_attribute_columns = []

        for index, user_account in enumerate(user_accounts):
            transfer_account = user_account.transfer_account
            if transfer_account:
                for jindix, column in enumerate(transfer_account_columns):
                    if column['query_type'] == 'db': cell_contents = "{0}".format(getattr(transfer_account, column['query']))
                    elif column['query'] == 'user_id': cell_contents = "{0}".format(transfer_account.primary_user.id)
                    elif column['query'] == 'first_name': cell_contents = "{0}".format(transfer_account.primary_user.first_name)
                    elif column['query'] == 'last_name': cell_contents = "{0}".format(transfer_account.primary_user.last_name)
                    elif column['query'] == 'phone': cell_contents = "{0}".format(transfer_account.primary_user.phone or '')
                    elif column['query'] == 'public_serial_number': cell_contents = "{0}".format(transfer_account.primary_user.public_serial_number or '')
                    elif column['query'] == 'location': cell_contents = "{0}".format(transfer_account.primary_user._location)
                    elif column['query'] == 'balance': cell_contents = getattr(transfer_account, column['query'])/100
                    elif column['query'] == 'has_beneficiary_role': cell_contents = "{0}".format(transfer_account.primary_user.has_beneficiary_role)
                    elif column['query'] == 'has_vendor_role': cell_contents = "{0}".format(transfer_account.primary_user.has_vendor_role)
                    elif include_sent_and_received:
                        if column['query'] == 'received':
                            received_amount = transfer_account.total_received
                            cell_contents = received_amount / 100
                        elif column['query'] == 'sent':
                            sent_amount = transfer_account.total_sent
                            cell_contents = sent_amount / 100
                    else:
                        cell_contents = ""
                    ws[index+2][jindix+1] = cell_contents
                if include_custom_attributes:
                    # Add custom attributes as columns at the end
                    for attribute in transfer_account.primary_user.custom_attributes:
                        name = (attribute.custom_attribute and attribute.custom_attribute.name) or ' '

                        try:
                            col_num = custom_attribute_columns.index(name) + 1 + len(transfer_account_columns)
                        except ValueError:
                            custom_attribute_columns.append(name)
                            col_num = len(custom_attribute_columns) + len(transfer_account_columns)
                        ws[index + 2][col_num] = attribute.value
            else:
                print('No Transfer Account for user account id: ', user_account.id)

        # Add custom attribute headers:
        if include_custom_attributes:
            for index, column_name in enumerate(custom_attribute_columns):
                ws[1][index + 1 + len(transfer_account_columns)] = column_name
    if include_transfers and user_accounts is not None:
        transfer_sheet = wb.new_sheet("credit_transfers")

        if user_type == 'all':
            transfers = CreditTransfer.query.enable_eagerloads(False).options(
                joinedload(CreditTransfer.transfer_usages).load_only(TransferUsage._name),
            )
        else:
            def _get_transfers_from_accounts(user_accounts):
                for u in user_accounts:
                    for transfer in u.transfer_account.credit_receives:
                        yield transfer
                    for transfer in u.transfer_account.credit_sends:
                        yield transfer
            transfers = _get_transfers_from_accounts(user_accounts)

        # Create credit_transfers workbook headers
        for index, column in enumerate(credit_transfer_columns):
            transfer_sheet[1][index+1] = column['header']

        used_transfers = set()
        for index, credit_transfer in enumerate(transfers):
            if credit_transfer.id not in used_transfers:
                used_transfers.add(credit_transfer.id)
                for jindix, column in enumerate(credit_transfer_columns):
                    if column['query_type'] == 'db':
                        cell_contents = "{0}".format(getattr(credit_transfer, column['query']))
                    elif column['query_type'] == 'enum':
                        enum = getattr(credit_transfer, column['query'])
                        cell_contents = "{0}".format(enum and enum.value)
                    elif column['query'] == 'transfer_amount':
                        cell_contents = "{0}".format(getattr(credit_transfer, column['query'])/100)
                    elif column['query'] == 'transfer_usages':
                        cell_contents = ', '.join([usage._name for usage in credit_transfer.transfer_usages])
                    else:
                        cell_contents = ""
                    transfer_sheet[index + 2][jindix + 1] = cell_contents
   
    file_url = export_workbook_via_s3(wb, workbook_filename)
    response_object = {
        'message': 'Export file created.',
        'data': {
            'file_url': file_url,
        }
    }
    return make_response(jsonify(response_object)), 201


class ExportAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()
        add_after_request_executor_job(generate_export, [post_data])
        return {
            'status': 'success',
            'data': {
                'message': 'Generating export. Please check your email shortly.',
            }
        }

class MeExportAPI(MethodView):
    @requires_auth
    def post(self):
        post_data = request.get_json()

        transfer_account = g.user.default_transfer_account or g.user.transfer_accounts[0]

        date_range = post_data.get('date_range')  # last day, previous week, or all
        email = post_data.get('email')

        credit_transfer_columns = [
            {'header': 'ID',                'query_type': 'db',     'query': 'id'},
            {'header': 'Transfer Amount',   'query_type': 'custom', 'query': 'transfer_amount'},
            {'header': 'Created',           'query_type': 'db',     'query': 'created'},
            {'header': 'Resolved Date',     'query_type': 'db',     'query': 'resolved_date'},
            {'header': 'Transfer Type',     'query_type': 'enum', 'query': 'transfer_type'},
            {'header': 'Transfer Status',   'query_type': 'enum', 'query': 'transfer_status'},
            {'header': 'Transfer Uses',     'query_type': 'custom',  'query': 'transfer_usages'},
        ]

        random_string = ''.join(random.choices(string.ascii_letters, k=5))
        export_time = str(datetime.utcnow())
        workbook_filename = 'vendor-id' + str(transfer_account.id) + '-' + str(export_time[0:10]) + '-' + random_string + '.xlsx'
        # e.g. vendor-id9-2018-09-19-adsff.xlsx

        # Vendor Export
        wb = Workbook()
        ws = wb.new_sheet("transfer_accounts")

        start_date = None
        end_date = None
        credit_transfer_list = []

        # Create credit_transfers workbook headers
        for index, column in enumerate(credit_transfer_columns):
            _ = ws[index + 1][1] = column['header']

        if date_range == 'day':
            # return previous day of transactions
            start_date = datetime.utcnow()
            end_date = start_date - timedelta(days=1)

        if date_range == 'week':
            # return previous week of transactions
            start_date = datetime.utcnow()
            end_date = start_date - timedelta(weeks=1)

        if start_date and end_date is not None:
            # filter by date_range & transfer_account.id
            credit_transfer_list = CreditTransfer.query.filter(
                and_(CreditTransfer.created.between(start_date, end_date), (
                or_(CreditTransfer.recipient_transfer_account_id == transfer_account.id,
                    CreditTransfer.sender_transfer_account_id == transfer_account.id))))\
                    .enable_eagerloads(False)
        else:
            # default to all credit transfers of transfer_account.id
            credit_transfer_list = CreditTransfer.query.filter(
                or_(CreditTransfer.recipient_transfer_account_id == transfer_account.id,
                    CreditTransfer.sender_transfer_account_id == transfer_account.id))\
                    .enable_eagerloads(False)
        credit_transfer_list = partition_query(credit_transfer_list)

        # loop over all credit transfers, create cells
        if credit_transfer_list is not None:
            for index, credit_transfer in enumerate(credit_transfer_list):
                for jindix, column in enumerate(credit_transfer_columns):
                    if column['query_type'] == 'db':
                        cell_contents = "{0}".format(getattr(credit_transfer, column['query']))
                    elif column['query_type'] == 'enum':
                        enum = getattr(credit_transfer, column['query'])
                        cell_contents = "{0}".format(enum and enum.value)
                    elif column['query'] == 'transfer_amount':
                        cell_contents = "{0}".format(getattr(credit_transfer, column['query']) / 100)
                    elif  column['query'] == 'transfer_usages':
                        cell_contents = ', '.join([usage.name for usage in credit_transfer.transfer_usages])
                    else:
                        cell_contents = ""
                    ws[jindix + 1][index + 2] = cell_contents

        if credit_transfer_list is not None:
            file_url = export_workbook_via_s3(wb, workbook_filename, email)

            response_object = {
                'status': 'success',
                'message': 'Export file created.',
                'file_url': file_url,
            }

            return make_response(jsonify(response_object)), 201

        else:
            # return no data
            response_object = {
                'status': 'Fail',
                'message': 'No data available for export',
                'file_url': '',
            }

            return make_response(jsonify(response_object)), 404


# add Rules for API Endpoints
export_blueprint.add_url_rule(
    '/export/',
    view_func=ExportAPI.as_view('export_view'),
    methods=['POST']
)

export_blueprint.add_url_rule(
    '/me/export/',
    view_func=MeExportAPI.as_view('me_export_view'),
    methods=['POST']
)
