# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

# Filter Types
USER = 'user'
CUSTOM_ATTRIBUTE = 'custom_attribute_user_storage'
TRANSFER_ACCOUNT = 'transfer_account'
CREDIT_TRANSFER = 'credit_transfer'
DATE = 'date'
ALL_FILTER_TYPES = [USER, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, CREDIT_TRANSFER, DATE]

# Timeseries Units
DAY = 'day'
WEEK = 'week'
MONTH = 'month'
YEAR = 'year'
TIMESERIES_UNITS = [DAY, WEEK, MONTH, YEAR]

# Metric Types
TRANSFER = 'credit_transfer'
USER = 'user'
ALL='all'
METRIC_TYPES = [TRANSFER, USER, ALL]

# Calculate timeseries per user
ADD_MISSING_DAYS = 'add_missing_days'
ADD_MISSING_DAYS_TO_TODAY = 'add_missing_days_to_today'
ACCUMULATE_TIMESERIES = 'accumulate_timeseries'
CALCULATE_TIMESERIES_PER_USER = 'calculate_timeseries_per_user'
CALCULATE_AGGREGATE_PER_USER = 'calculate_aggregate_per_user'
CALCULATE_TOTAL_PER_USER = 'calculate_total_per_user'
FORMAT_TIMESERIES = 'format_timeseries'
FORMAT_AGGREGATE_METRICS = 'format_aggregate_metrics'
GET_FIRST = 'get_first'

TIMESERIES_ACTIONS = [
    ADD_MISSING_DAYS, 
    ADD_MISSING_DAYS_TO_TODAY, 
    ACCUMULATE_TIMESERIES, 
    CALCULATE_TIMESERIES_PER_USER,
    CALCULATE_AGGREGATE_PER_USER,
    CALCULATE_TOTAL_PER_USER,
    FORMAT_TIMESERIES, 
    FORMAT_AGGREGATE_METRICS,
    GET_FIRST
]

# Group by values
GENDER = 'gender'
TRANSFER_TYPE = 'transfer_type'
TRANSFER_MODE = 'transfer_mode'
ACCOUNT_TYPE = 'account_type'
TRANSFER_SUBTYPE = 'transfer_subtype'
TRANSFER_STATUS = 'transfer_status'
TRANSFER_USAGE = 'transfer_usage'
GROUP_BY_TYPES = [GENDER, TRANSFER_TYPE, TRANSFER_MODE, ACCOUNT_TYPE, TRANSFER_SUBTYPE, TRANSFER_STATUS, TRANSFER_USAGE]

# Misc Values
GROUPED = 'grouped'
UNGROUPED = 'ungrouped'
