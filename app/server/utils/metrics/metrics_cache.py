# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from datetime import datetime, timedelta

from server import red, db
from flask import g
from decimal import Decimal
import json
import pickle
import config

SUM = 'SUM'
SUM_OBJECTS ='SUM_OBJECTS'
COUNT ='COUNT'
FIRST_COUNT = 'FIRST_COUNT'
QUERY_ALL = 'QUERY_ALL'

valid_strategies = [SUM, COUNT, SUM_OBJECTS, FIRST_COUNT, QUERY_ALL]
# Combinatory stategies which aren't cachable
dumb_strategies = [FIRST_COUNT, QUERY_ALL]

def _store_cache(key, value):
    pickled_object = pickle.dumps(value)
    red.set(key, pickled_object, config.METRICS_CACHE_TIMEOUT)
    return True

def _load_cache(key):
    cached_object = red.get(key)
    if not cached_object:
        return None
    try:
        return pickle.loads(cached_object)
    except:
        red.delete(key)
        return None

def get_metrics_org_string(org_id):
    return str(org_id)+'_metrics_'


def execute_with_partial_history_cache(metric_name, query, object_model, strategy, enable_cache = True, group_by=None):
    clear_metrics_cache()
    # enable_cache pass-thru. This is so we don't cache data when filters are active.
    if strategy in dumb_strategies or not enable_cache:
        return _handle_combinatory_strategy(query, None, strategy)

    # Redis object names
    if g.get('query_organisations'):
        ORG_STRING = get_metrics_org_string(g.query_organisations)
    else:
        ORG_STRING = get_metrics_org_string(g.active_organisation.id)
    CURRENT_MAX_ID = f'{ORG_STRING}_{object_model.__table__.name}_max_id'
    HIGHEST_ID_CACHED = f'{ORG_STRING}_{metric_name}_{group_by}_max_cached_id'
    CACHE_RESULT = f'{ORG_STRING}_{metric_name}_{group_by}'

    # Checks if provided combinatry strategy is valid
    if strategy not in valid_strategies:
        raise Exception(f'Invalid combinatory strategy {strategy} requested.')

    # Getting the current maximum ID in the database. Also caching it so we don't have to
    # get it from the DB many times in the same request
    current_max_id = red.get(CURRENT_MAX_ID)
    if not current_max_id:
        query_max = db.session.query(db.func.max(object_model.id)).first()
        try:
            current_max_id = query_max[0]
        except IndexError:
            current_max_id = 0

        red.set(CURRENT_MAX_ID, current_max_id, 10)

    # Gets cache results since the last time the metrics were fetched
    highest_id_in_cache = int(red.get(HIGHEST_ID_CACHED) or 0)
    cache_result = _load_cache(CACHE_RESULT)
    # If there's no cache (either it's a new attribute we're tracking, or the cache is corrupted)
    # then we should pull results starting at id=0
    if cache_result:
        filtered_query = query.filter(object_model.id > highest_id_in_cache)
    else:
        filtered_query = query

    #Combines results
    result = _handle_combinatory_strategy(filtered_query, cache_result, strategy)

    # Updates the cache with new data
    _store_cache(CACHE_RESULT, result)
    red.set(HIGHEST_ID_CACHED, current_max_id, config.METRICS_CACHE_TIMEOUT)

    return result
    
# Nukes metrics cache for the active org, returns number of deleted entries!
def clear_metrics_cache():
    if g.get('query_organisations'):
        ORG_STRING = get_metrics_org_string(g.query_organisations)
    else:
        ORG_STRING = get_metrics_org_string(g.active_organisation.id)
    keys = red.keys(ORG_STRING+'*')
    key_count = len(keys)
    for key in keys:
        red.delete(key)
    return key_count

def _handle_combinatory_strategy(query, cache_result, strategy):
    return strategy_functions[strategy](query, cache_result)

def _sum_strategy(query, cache_result):
    return float(query.first().total or 0) + (cache_result or 0)

def _count_strategy(query, cache_result):
    return query.count() + (cache_result or 0)

def _sum_list_of_objects(query, cache_result):
    combined_results = {}
    for r in cache_result or []:
        if r[0]:
            if len(r) == 3:
                combined_results[(r[1], r[2])] = r[0]
            else:
                combined_results[(r[1])] = r[0]

    query_result = query.all()
    for r in query_result:
        if len(r) == 3:
            if (r[1], r[2]) not in combined_results:
                combined_results[(r[1], r[2])] = r[0]
            else:
                combined_results[(r[1], r[2])] += r[0]
        else:
            if r[1] not in combined_results:
                combined_results[(r[1])] = r[0]
            else:
                combined_results[(r[1])] += r[0]

    formatted_results = []
    for result in combined_results:
        if isinstance(result, tuple) and len(result) == 2:
            formatted_results.append((combined_results[(result[0], result[1])], result[0], result[1
            ]))
        else:
            formatted_results.append((combined_results[(result)], result))

    return formatted_results

# "Dumb" combinatory strategies which are uncachable
def _first_count(query, cache_result):
    return query.first().count

def _return_all(query, cache_result):
    return query.all()

strategy_functions = { SUM: _sum_strategy, COUNT: _count_strategy, SUM_OBJECTS: _sum_list_of_objects, FIRST_COUNT: _first_count, QUERY_ALL: _return_all }
