from datetime import datetime, timedelta

from server import red, db
from flask import g
from decimal import Decimal
import json
import pickle

SUM = 'SUM'
SUM_OBJECTS ='SUM_OBJECTS'
COUNT ='COUNT'

valid_strategies = [SUM, COUNT, SUM_OBJECTS]

def _store_cache(key, value):
    pickled_object = pickle.dumps(value)
    red.set(key, pickled_object)
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

def execute_with_partial_history_cache(metric_name, query, object_model, strategy, disable_cache = False):
    # disable_cache pass-thru. This is so we don't cache data when filters are active.
    if disable_cache:
        return _handle_combinatory_strategy(query, None, strategy)

    # Redis object names
    if g.get('query_organisations'):
        ORG_STRING = str(g.query_organisations)
    else:
        ORG_STRING = str(g.active_organisation.id)
    CURRENT_MAX_ID = f'{ORG_STRING}_{object_model.__table__.name}_max_id'
    HIGHEST_ID_CACHED = f'{ORG_STRING}_{metric_name}_max_cached_id'
    CACHE_RESULT = f'{ORG_STRING}_{metric_name}'

    # Checks if provided combinatry strategy is valid
    if strategy not in valid_strategies:
        raise Exception(f'Invalid combinatory strategy {strategy} requested.')

    # Getting the current maximum ID in the database. Also caching it so we don't have to
    # get it from the DB many times in the same request
    current_max_id = red.get(CURRENT_MAX_ID)
    if not current_max_id:
        current_max_id = db.session.query(db.func.max(object_model.id)).first() or (0, )
        current_max_id = current_max_id[0]
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
    red.set(HIGHEST_ID_CACHED, current_max_id)

    return result

def _handle_combinatory_strategy(query, cache_result, strategy):
    return strategy_functions[strategy](query, cache_result)

def _sum_strategy(query, cache_result):
    return float(query.first().total or 0) + (cache_result or 0)

def _count_strategy(query, cache_result):
    return query.count() + (cache_result or 0)

def _sum_list_of_objects(query, cache_result):
    combined_results = {}
    for r in cache_result or []:
        combined_results[r[1]] = r[0]
    query_result = query.all()

    for r in query_result:
        if r[1] not in combined_results:
            combined_results[r[1]] = r[0]
        else:
            combined_results[r[1]] = combined_results[r[1]] + r[0]
    
    formatted_results = []
    for result in combined_results:
        formatted_results.append((combined_results[result], result))
    return formatted_results

strategy_functions = { SUM: _sum_strategy, COUNT: _count_strategy, SUM_OBJECTS: _sum_list_of_objects }
