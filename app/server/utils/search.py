from sqlalchemy.sql.expression import func

from server import db
from server.utils.metrics.filters import apply_filters
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from functools import reduce
from sqlalchemy.orm import lazyload, aliased

class SearchableColumn:
    def __init__(self, name, column, rank=1):
        self.name = name
        self.column = column
        self.rank = rank

    def get_similarity_query(self, query):
        return (func.coalesce(func.similarity(self.column, query), 0).label('rank') * self.rank)

TRANSFER_ACCOUNT = 'TRANSFER_ACCOUNT'
CREDIT_TRANSFER = 'CREDIT_TRANSFER'

def generate_search_query(search_string, filters, order, sort_by_arg, include_user=False, search_type=TRANSFER_ACCOUNT):
    """
    Generates query to search transfer accounts by their users' parameters. This is used by search_api, as well as
    the bulk disbursement API
    :param search_string - The search query string
    :param filters - A SQLAlchemy filter object to apply to the query
    :param order - Which order in which to display results. Use sqlalchemy.asc or sqlalchemy.desc
    :param sort_by_arg: Boolean. True returns original phone
    """
    sender = aliased(User)
    recipient = aliased(User)
    sort_types_to_database_types = {
        TRANSFER_ACCOUNT: {
            'first_name': User.first_name,
            'last_name': User.last_name,
            'email': User.email,
            'date_account_created': User.created,
            'rank': 'rank',
            'balance': TransferAccount._balance_wei,
            'status': TransferAccount.is_approved,
        },
        CREDIT_TRANSFER: {
            'sender_first_name': sender.last_name,
            'sender_last_name': sender.last_name,
            'recipient_first_name': recipient.last_name,
            'recipient_last_name': recipient.last_name,
            'amount': CreditTransfer._transfer_amount_wei,
            'created': CreditTransfer.created,
            'id': CreditTransfer.id,
            'rank': 'rank',
        }
    }

    if sort_by_arg not in sort_types_to_database_types[search_type]:
        return {
            'message': f'Invalid sort_by value {sort_by_arg}. Please use one of the following: {sort_types_to_database_types[search_type].keys()}'\
        }
    # To add new searchable column, simply add a new SearchableColumn object!
    # And don't forget to add a trigram index on that column too-- see migration 33df5e72fca4 for reference
    user_search_columns = [
        SearchableColumn('first_name', User.first_name, rank=1.5),
        SearchableColumn('last_name', User.last_name, rank=1.5),
        SearchableColumn('phone', User.phone, rank=2),
        SearchableColumn('public_serial_number', User.public_serial_number, rank=2),
        SearchableColumn('location', User.location, rank=1),
        SearchableColumn('primary_blockchain_address', User.primary_blockchain_address, rank=2),
    ]
    sum_search = reduce(lambda x,y: x+y, [sc.get_similarity_query(search_string) for sc in user_search_columns])
    sort_by = sum_search if sort_by_arg == 'rank' else sort_types_to_database_types[sort_types_to_database_types][sort_by_arg]
    # If there's no search string, the process is the same, just sort by account creation date
    if search_type == TRANSFER_ACCOUNT:
        sort_by = sort_types_to_database_types[sort_types_to_database_types]['date_account_created'] if sort_by == 'rank' and not search_string else sort_by
        entities = [TransferAccount, sum_search, User] if include_user else [TransferAccount]
        final_query = db.session.query(TransferAccount, User, sum_search)\
            .outerjoin(TransferAccount, User.default_transfer_account_id == TransferAccount.id)\
            .filter(TransferAccount.is_ghost != True) \
            .with_entities(*entities)\
            .order_by(order(sort_by))
        # Joining custom attributes is quite expensive, and we don't need them in a listing of search results
        if include_user:
            final_query = final_query.options(lazyload(User.custom_attributes))

    else:
        sort_by = sort_types_to_database_types[sort_types_to_database_types]['created'] if sort_by == 'rank' and not search_string else sort_by

        final_query = db.session.query(CreditTransfer, sum_search)\
            .join(CreditTransfer, User.id == CreditTransfer.recipient_user_id or User.id == CreditTransfer.sender_user_id)\
            .join(sender, sender.id == CreditTransfer.sender_user_id)\
            .join(recipient, recipient.id == CreditTransfer.recipient_user_id)\
            .with_entities(CreditTransfer, User, sum_search)\
            .order_by(order(sort_by))\
            .limit(10)
    
    # If there is a search string, we only want to return ranked results!
    final_query = final_query.filter(sum_search!=0) if search_string else final_query
    if search_type == CREDIT_TRANSFER:
        return apply_filters(final_query, filters, CreditTransfer)
    if search_type == TRANSFER_ACCOUNT:
        return apply_filters(final_query, filters, User)
