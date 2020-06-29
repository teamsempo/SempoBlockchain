def calculate_total_beneficiaries(disable_cache=disable_cache):
    total_beneficiaries = db.session.query(User).filter(*beneficiary_filters)
    return metrics_cache.execute_with_partial_history_cache('total_beneficiaries', total_beneficiaries, CreditTransfer, metrics_cache.COUNT, disable_cache=disable_cache)

def calculate_total_vendors(disable_cache=disable_cache):
    total_vendors = db.session.query(User).filter(*vendor_filters)
    return metrics_cache.execute_with_partial_history_cache('total_vendors', total_vendors, CreditTransfer, metrics_cache.COUNT, disable_cache=disable_cache)

def calculate_total_users():
    return calculate_total_beneficiaries() + calculate_total_vendors()

def calculate_has_transferred_count():
    return db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id))
        .label('transfer_count'))\
        .filter(*standard_payment_filters) \
        .filter(*date_filter) \
            .first().transfer_count
