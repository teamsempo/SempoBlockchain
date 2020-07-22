# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from server import db, red, bt

from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.utils.metrics import filters, metrics_cache, metric
from server.utils.metrics.metrics_const import *

filterable_attributes = [DATE, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, USER]

total_beneficiaries_query = db.session.query(User)
total_beneficiaries = metric.Metric(
    metric_name='total_beneficiaries', 
    query=total_beneficiaries_query, 
    object_model=User, 
    stock_filters=[filters.beneficiary_filters], 
    caching_combinatory_strategy=metrics_cache.COUNT,
    filterable_by=filterable_attributes)

total_vendors_query = db.session.query(User)
total_vendors = metric.Metric(
    metric_name='total_vendors', 
    query=total_vendors_query, 
    object_model=User, 
    stock_filters=[filters.vendor_filters], 
    caching_combinatory_strategy=metrics_cache.COUNT,
    filterable_by=filterable_attributes)


