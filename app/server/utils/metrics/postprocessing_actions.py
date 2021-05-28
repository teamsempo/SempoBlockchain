from datetime import date, timedelta, datetime
from server.utils.metrics.metrics_const import *

VALUE = 'value'

# Sometimes group names can have quotation marks, be None, or be an enum
# This turns them into readable strings for the API!
def _format_group_name(group_name):
    if not group_name:
        return 'None'
    try:
        # Sometimes group_name can be an enum. Ugly hack to get the enum's value in this case
        return group_name.value
    except:
        # Custom attributes contain quotation marks we don't need. Ugly hack #2
        return group_name.replace('"', "")

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
        for i in range(delta.days + 2):
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
def calculate_timeseries_per_user(query_result, population_query_result):
    if GROUPED in population_query_result:
        is_grouped = True
        population_query_result = population_query_result[GROUPED]
    else:
        is_grouped = False
        population_query_result = population_query_result[UNGROUPED]

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
    last_successful_population_lookup = None
    for result in query_result:
        # If population_query_result is grouped we want to divide our result by the population of the relevant group
        # Otherwise, the total population is the product

        if is_grouped:
            index = result[2]
        else:
            index = VALUE

        try:
            last_successful_population_lookup = population_dates[result[1]]
            if last_successful_population_lookup[index] != 0:
                product = result[0] / (last_successful_population_lookup[index])
            else:
                product = 0
        except KeyError as e:
            # Makes the data slightly more robust to missing info
            # by allowing us to fallback to the last population info
            if last_successful_population_lookup:
                product = result[0] / last_successful_population_lookup[index] if index in last_successful_population_lookup else 0
            else:
                product = 0

        if len(result) > 2 and result[2]:
            results_per_user.append((product, result[1], result[2]))
        else:
            results_per_user.append((product, result[1]))
    return results_per_user

# Similar to calculate_timeseries_per_user, but for aggregate queries
# Input (query_result):  [(2, 'apples'), (20, 'bananas)]
# Input (population_query_result):  [(10, 01/01/2020), (10, 01/02/2020), (10, 01/03/2020), (20, 01/04/2020) (20, 01/05/2020)]
# Output: [(.1, 'apples'), (1, 'bananas)]
def calculate_aggregate_per_user(query_result, population_query_result):
    result = []
    last_day = population_query_result[UNGROUPED][-1][1]
    if GROUPED in population_query_result:
        category_populations = {}
        for pqr in population_query_result[GROUPED]:
            if pqr[1] == last_day:
                category_populations[pqr[2]] = pqr[0]
        for r in query_result:
            if r[1] in category_populations:
                result.append((r[0]/category_populations[r[1]], r[1]))
            else:
                result.append((0, r[1]))
        return result
    
    elif UNGROUPED in population_query_result:
        last_day_population = population_query_result[UNGROUPED][-1][0]
    else:
        last_day_population = 1    
    for r in query_result:
        result.append((r[0]/last_day_population, r[1]))
    return result

# Similar to calculate_timeseries_per_user, but for totals
# Input (query_result):  2
# Input (population_query_result):  [(10, 01/01/2020), (10, 01/02/2020), (10, 01/03/2020), (20, 01/04/2020) (20, 01/05/2020)]
# Output: 0.2
def calculate_total_per_user(query_result, population_query_result):
    if population_query_result[UNGROUPED]:
        last_day_population = population_query_result[UNGROUPED][-1][0]
    else:
        last_day_population = 1
    query_result = query_result or 0
    return query_result/last_day_population

# Final step in formatting the timeseries data to be in a format 
# which once JSONified, the API expects. 
# Input (query_result): [(10, 01/01/2020), (20, 01/02/2020)]
# Output: [{'date': '2020-01-01T00:00:00', 'volume': 10}, {'date': '2020-01-02T00:00:00', 'volume': 10}]
# NOTE: Expect this to change a bit in the upcoming GROUP_BY PR
# Schema preview: https://sempo.slack.com/archives/CLH7NENGJ/p1595505964026900
def format_timeseries(query_result, population_query_result):
    data_by_groups = {}
    for r in query_result:
        if len(r) < 3:
            group_name='None'
        else:
            group_name = _format_group_name(r[2])
        if not group_name:
            group_name = 'None'
        try:
            # Sometimes group_name can be an enum. Ugly hack to get the enum's value in this case
            group_name = group_name.value
        except:
            pass
        date = r[1]
        value = r[0]
        if group_name not in data_by_groups:
            data_by_groups[group_name] = []
        data_by_groups[group_name].append({'date': date.isoformat(), VALUE: value})
    return data_by_groups

# Changes sqlalchemy raw output into the shape expected for the API!
def format_aggregate_metrics(query_result, population_query_result):
    result = {}
    for r in query_result:
        result[_format_group_name(r[1])] = r[0]
    return result

# Some singleton metrics are returned in a tuple in a list. This unpacks and handles nulls
def get_first(query_result, population_query_result):
    if query_result:
        if not query_result[0][0]:
            return 0 # query_result[0][0] can be null, which means 0 for our context
        return query_result[0][0]
    else:
        return 0

query_actions = {
    ADD_MISSING_DAYS: add_missing_days,
    ADD_MISSING_DAYS_TO_TODAY: add_missing_days_to_today,
    ACCUMULATE_TIMESERIES: accumulate_timeseries,
    CALCULATE_TIMESERIES_PER_USER: calculate_timeseries_per_user,
    CALCULATE_AGGREGATE_PER_USER: calculate_aggregate_per_user,
    CALCULATE_TOTAL_PER_USER: calculate_total_per_user,
    FORMAT_TIMESERIES: format_timeseries,
    FORMAT_AGGREGATE_METRICS: format_aggregate_metrics,
    GET_FIRST: get_first,
}

# Executes query_actions against query results
# These are done in the order they're declared in the Metric object
# so you can chain together common actions and reuse them across metrics!
def execute_postprocessing(query_result, population_query_result = None, actions = None):
    for action in actions:
        if action not in TIMESERIES_ACTIONS:
            raise Exception(f'{action} not a valid timeseries action')
        query_result = query_actions[action](query_result, population_query_result)
    return query_result
