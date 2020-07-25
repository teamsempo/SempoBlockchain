# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

USER = 'user'
CUSTOM_ATTRIBUTE = 'custom_attribute_user_storage'
TRANSFER_ACCOUNT = 'transfer_account'
CREDIT_TRANSFER = 'credit_transfer'
DATE = 'date'
ALL_FILTER_TYPES = [USER, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, CREDIT_TRANSFER, DATE]

DAY = 'day'
WEEK = 'week'
MONTH = 'month'
YEAR = 'year'
TIMESERIES_UNITS = [DAY, WEEK, MONTH, YEAR]

TRANSFER = 'transfer'
USER = 'user'
ALL='all'
METRIC_TYPES = [TRANSFER, USER, ALL]

# Calculate timeseries per user
ADD_MISSING_DAYS = 'add_missing_days'
ADD_MISSING_DAYS_TO_TODAY = 'add_missing_days_to_today'
ACCUMULATE_TIMESERIES = 'accumulate_timeseries'
CALCULATE_PER_USER = 'calculate_per_user'
FORMAT_TIMESERIES = 'format_timeseries'
AGGREGATE_FORMATTED_TIMESERIES = 'AGGREGATE_FORMATTED_TIMESERIES'
TIMESERIES_ACTIONS = [ADD_MISSING_DAYS, ADD_MISSING_DAYS_TO_TODAY, ACCUMULATE_TIMESERIES, CALCULATE_PER_USER, FORMAT_TIMESERIES, AGGREGATE_FORMATTED_TIMESERIES]

