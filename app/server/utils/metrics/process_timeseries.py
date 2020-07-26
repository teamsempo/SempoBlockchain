# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from datetime import date, timedelta, datetime
from server.utils.metrics.metrics_const import *

VALUE = 'value'

# Takes sorted list of tuples where the 2nd element is a date, and fills in the gaps
# Example:
# Input:  [(5, 01/01/2020), (10, 01/04/2020)] 
# Output: [(5, 01/01/2020), (0, 01/02/2020), (0, 01/03/2020), (0, 01/04/2020)] 
def add_missing_days(query_result, population_query_result=None, end_date=None):
    if not query_result:
        return query_result
    # Determine date range
    start_date = query_result[0][1]
    if not end_date:
        end_date = query_result[-1][1]
    delta = end_date - start_date

    # If it's a grouped query result, build a set of groups
    is_grouped = False
    if query_result and len(query_result[0]) != 2:
        is_grouped = True
    group_set = None
    if is_grouped:
        group_set = set()
        for r in query_result:
            group_set.add(r[2])   

    # Make lookup table to get users of a specific group from a specific day
    days_to_results = {}
    for qr in query_result:
        date = qr[1]
        value = qr[0]
        group_name = VALUE
        if is_grouped:
            group_name = qr[2]

        if date not in days_to_results:
            days_to_results[date] = {group_name: value}
        else:
            days_to_results[date][group_name] = value

    full_date_range = []
    for group in group_set or [group_name]:
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if day in days_to_results:
                if group in days_to_results[day]:
                    value = days_to_results[day][group]
                    full_date_range.append((value, day, group))
                else:
                    full_date_range.append((0, day, group))
            else:
                full_date_range.append((0, day, group))

    # Turn throuple into tuple if not grouped 
    if not is_grouped:
        full_date_range = [(value, day) for value, day, group in full_date_range]
    full_date_range.sort(key=lambda x:x[1])
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
    accumulator = {}
    accumulated_result = []
    is_grouped = True
    if query_result and len(query_result[0]) == 2:
        accumulator['total'] = 0
        is_grouped = False
    for qr in query_result:
        date = qr[1]
        value = qr[0]
        group_name = VALUE
        if is_grouped:
            group_name = qr[2]
            if group_name not in accumulator:
                accumulator[group_name] = 0
            accumulated_element = (value+accumulator[group_name], date, group_name)
            accumulator[group_name] += value
        else:
            accumulated_element = (value+accumulator['total'], date)
            accumulator['total'] += value
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
    is_grouped = True
    if population_query_result and len(population_query_result[0]) == 2:
        is_grouped = False
    # Make dict to lookup the relevant population
    population_dates = {}
    for pqr in population_query_result:
        date = pqr[1]
        value = pqr[0]
        group = VALUE
        if is_grouped:
           group = pqr[2] 
        if date not in population_dates:
            population_dates[date] = {}
        population_dates[date][group] = value

    results_per_user = []
    last_succesful_population_lookup = None
    for result in query_result:
        # If population_query_result is grouped we want to divide our result by the population of the relevant group
        # Otherwise, the total population is the product
        if is_grouped:
            product = result[0]/population_dates[result[1]][result[2]]
        else:
            try:
                last_succesful_population_lookup = population_dates[result[1]]

                denominator = last_succesful_population_lookup[VALUE]

            except KeyError as e:
                # Makes the data slightly more robust to missing info
                # by allowing us to fallback to the last population info
                if last_succesful_population_lookup:
                    denominator = last_succesful_population_lookup[VALUE]
                else:
                    denominator = 1

            product = result[0] / denominator

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
        data_by_groups[group_name].append({'date': date.isoformat(), VALUE: value})
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
            group_total += value[VALUE]
            overall_total += value[VALUE]
        totals[group] = group_total
    totals['total'] = overall_total
    return { 'timeseries': query_result, 'aggregate': totals }

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
