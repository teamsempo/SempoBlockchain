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
TRANSFER_TYPE = 'transfer_type'
TRANSFER_MODE = 'transfer_mode'
TRANSFER_STATUS = 'transfer_status'
TRANSFER_USAGE = 'transfer_usage'
SENDER_LOCATION = 'sender,location'
SENDER_ACCOUNT_TYPE = 'sender,account_type'
SENDER_COOORDINATES = 'sender,coordinates'
RECIPIENT_LOCATION = 'recipient,location'
RECIPIENT_ACCOUNT_TYPE = 'recipient,account_type'
RECIPIENT_COOORDINATES = 'recipient,coordinates'

UNGROUPED = 'ungrouped'


# Misc Values
GROUPED = 'grouped'

# Metric types
COUNT = 'count'
COUNT_AVERAGE = 'count_average'
CURRENCY = 'currency'
VALUE_TYPES = [COUNT, COUNT_AVERAGE, CURRENCY]
