from datetime import date, timedelta
from server.utils.metrics.metrics_const import *


# TODO: Mechanism to get population at day0 if there's a lower bound date filter

# Takes sorted list of tuples where the 2nd element is a date, and fills in the gaps
# Example:
# Input:  [(5, 01/01/2020, (10, 01/04/2020)] 
# Output: [(5, 01/01/2020), (0, 01/02/2020), (0, 01/03/2020), (0, 01/04/2020) (10, 01/05/2020)] 
# TODO: Make it generic (day/week/month/year)
def add_missing_days(query_result, population_query_result=None):
    start_date = query_result[0][1]
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
    population_dates = {}
    for pqr in population_query_result:
        population_dates[pqr[1]] = pqr[0]
    results_per_user = []
    for result in query_result:
        product = result[0]/population_dates[result[1]]
        results_per_user.append((product, result[1]))
    return results_per_user


timeseries_actions = {
    ADD_MISSING_DAYS: add_missing_days,
    ACCUMULATE_TIMESERIES: accumulate_timeseries,
    CALCULATE_PER_USER: calculate_per_user
}

def process_timeseries(query_result, population_query_result = None, actions = None):
    print(actions)
    print(actions)
    print(actions)
    print(actions)
    for action in actions:
        if action not in TIMESERIES_ACTIONS:
            raise Exception(f'{action} not a valid timeseries action')
        timeseries_actions[action](query_result, population_query_result)