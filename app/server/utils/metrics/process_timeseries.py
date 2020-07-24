# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from datetime import date, timedelta, datetime
from server.utils.metrics.metrics_const import *

# Takes sorted list of tuples where the 2nd element is a date, and fills in the gaps
# Example:
# Input:  [(5, 01/01/2020), (10, 01/04/2020)] 
# Output: [(5, 01/01/2020), (0, 01/02/2020), (0, 01/03/2020), (0, 01/04/2020)] 
def add_missing_days(query_result, population_query_result=None, end_date=None):
    if not query_result:
        return query_result
    start_date = query_result[0][1]
    if not end_date:
        end_date = query_result[-1][1]
    delta = end_date - start_date

    if len(query_result) >=1:
        comparator = query_result.pop(0)

    full_date_range = []
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)

        if (day - comparator[1]).days == 0:
            full_date_range.append(comparator) 
            if len(query_result) >=1:
                comparator = query_result.pop(0)
        else:
            full_date_range.append((0, day))   
    return full_date_range

# add_missing_days, but goes to today instead of filling out the whole range
def add_missing_days_to_today(query_result, population_query_result=None):
    return add_missing_days(query_result, end_date=datetime.now())

# Takes sorted list of tuples where the 2nd element is a date, and accumulates the numbers in the first elements
# Example:
# Input:  [(5, 01/01/2020), (1, 01/02/2020), (2, 01/03/2020), (0, 01/04/2020) (3, 01/05/2020)]
# Output: [(5, 01/01/2020), (6, 01/02/2020), (8, 01/03/2020), (8, 01/04/2020) (11, 01/05/2020)] 
# TODO: Make it generic (day/week/month/year)
def accumulate_timeseries(query_result, population_query_result=None):
    acc = 0
    accumulated_result = []
    for qr in query_result:
        accumulated_element = (qr[0]+acc, qr[1])
        acc += qr[0]
        accumulated_result.append(accumulated_element)
    return accumulated_result

# Takes two sorted lists of tuples where the 2nd element is a date, and accumulates the numbers in the first elements
# List 1: query_result: An example of this might be for number_of_trades
# List 1: population_query_result: Typically this will be the total number of users
# Example:
# Input (query_result):  [(10, 01/01/2020), (20, 01/02/2020), (10, 01/03/2020), (30, 01/04/2020) (20, 01/05/2020)]
# Input (population_query_result):  [(10, 01/01/2020), (10, 01/02/2020), (10, 01/03/2020), (20, 01/04/2020) (20, 01/05/2020)]
# Output: [(1, 01/01/2020), (2, 01/02/2020), (1, 01/03/2020), (1.333, 01/04/2020) (1, 01/05/2020)] 
def calculate_per_user(query_result, population_query_result):
    # TODO: Do we want to group the whole population too?
    return query_result
    population_dates = {}
    for pqr in population_query_result:
        population_dates[pqr[1]] = pqr[0]
    results_per_user = []
    for result in query_result:
        product = result[0]/population_dates[result[1]]
        if result[2]:
            results_per_user.append((product, result[1], result[2]))
        else:
            results_per_user.append((product, result[1]))
    return results_per_user

# Final step in formatting the timeseries data to be in a format 
# which once JSONified, the API expects. 
# Input (query_result): [(10, 01/01/2020), (20, 01/02/2020)]
# Output: [{'date': '2020-01-01T00:00:00', 'volume': 10}, {'date': '2020-01-02T00:00:00', 'volume': 10}]
# NOTE: Expect this to change a bit in the upcoming GROUP_BY PR
# Schema preview: https://sempo.slack.com/archives/CLH7NENGJ/p1595505964026900
def format_timeseries(query_result, population_query_result):
    data_by_groups = {}
    for r in query_result:
        group_name = r[2]
        if not group_name:
            group_name = 'None'
        try:
            # Sometimes group_name can be an enum. Ugly hack to get the enum's value in this case
            group_name = group_name.value
        except:
            # Custom attributes contain quotation marks we don't need. Ugly hack #2
            group_name = group_name.replace('"', "")
        date = r[1]
        value = r[0]
        if group_name not in data_by_groups:
            data_by_groups[group_name] = []
        data_by_groups[group_name].append({'date': date.isoformat(), 'value': value})
    return data_by_groups

# Input (query_result): [{'date': '2020-01-01T00:00:00', 'volume': 10}, {'date': '2020-01-02T00:00:00', 'volume': 10}]
# Output: {'timeseries': [{'date': '2020-01-01T00:00:00', 'volume': 10}, {'date': '2020-01-02T00:00:00', 'volume': 10}],
#           'aggregate': {'total': 20} }
def aggregate_formatted_timeseries(query_result, population_query_result):
    totals = {}
    overall_total = 0
    for group in query_result:
        group_total = 0
        for value in query_result[group]:
            group_total += value['value']
            overall_total += value['value']
        totals[group] = group_total
    totals['total'] = overall_total
    return { 'timeseries': query_result, 'aggregate': totals }
    #total = 0
    #for qr in query_result:
    #    total += qr['volume']

timeseries_actions = {
    ADD_MISSING_DAYS: add_missing_days,
    ADD_MISSING_DAYS_TO_TODAY: add_missing_days_to_today,
    ACCUMULATE_TIMESERIES: accumulate_timeseries,
    CALCULATE_PER_USER: calculate_per_user,
    FORMAT_TIMESERIES: format_timeseries,
    AGGREGATE_FORMATTED_TIMESERIES: aggregate_formatted_timeseries,
}

# Executes timeseries_actions against query results
# These are done in the order they're declared in the Metric object
# so you can chain together common actions and reuse them across metrics!
def process_timeseries(query_result, population_query_result = None, actions = None):
    for action in actions:
        if action not in TIMESERIES_ACTIONS:
            raise Exception(f'{action} not a valid timeseries action')
        query_result = timeseries_actions[action](query_result, population_query_result)
    return query_result
