from datetime import datetime, timedelta
import math
import calendar

def find_last_period_dates(epoch_datetime, target_datetime, period_type, period_length = 1):

    if period_type == 'days':
        days_elapsed = diff_day(target_datetime, epoch_datetime)
        periods_elapsed = math.floor(days_elapsed / period_length)

        prior_period_end = epoch_datetime + timedelta(days=periods_elapsed * period_length)

        prior_period_start = prior_period_end - timedelta(days=period_length)

    elif period_type == 'week':
        weeks_elapsed = diff_week(target_datetime, epoch_datetime)
        periods_elapsed = math.floor(weeks_elapsed / period_length)

        prior_period_end = epoch_datetime + timedelta(weeks=periods_elapsed * period_length)

        prior_period_start = prior_period_end - timedelta(weeks=period_length)

    else: #default to months
        months_elapsed = diff_month(target_datetime, epoch_datetime)
        periods_elapsed = math.floor(months_elapsed / period_length)

        prior_period_start = add_months(epoch_datetime, (periods_elapsed - 1) * period_length)

        prior_period_end = add_months(prior_period_start, period_length)

    return prior_period_start, prior_period_end

def diff_day(d1, d2):
    return (d1 - d2).days


def diff_week(d1, d2):
    days = (d1 - d2).days
    return math.floor(days/7)

def diff_month(d1, d2):

    months = (d1.year - d2.year) * 12 + d1.month - d2.month

    if d1.day < d2.day:
        return months - 1
    else:
        return months


def add_months(date, months):
    months_count = date.month + months

    # Calculate the year
    year = date.year + int(months_count / 12)

    # Calculate the month
    month = (months_count % 12)
    if month == 0:
        month = 12

    # Calculate the day
    day = date.day
    last_day_of_month = calendar.monthrange(year, month)[1]
    if day > last_day_of_month:
        day = last_day_of_month

    new_date = datetime(year, month, day)
    return new_date

#
# date = datetime(2018, 11, 30)
#
# # print(date, add_months(date, -3))
#
#
# today = datetime.utcnow()
#
# d_0 = datetime(2018,1,22)
#
# dates = find_last_period_dates(d_0, today, {'type': 'month', 'length': 6})
# print(dates)