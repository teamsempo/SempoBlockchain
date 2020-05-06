from datetime import datetime, timedelta

from server import red, db
from flask import g
from decimal import Decimal
import json
import pickle

SUM = 'SUM'
SUM_OBJECTS ='SUM_OBJECTS'
TIMESERIES ='TIMESERIES'
COUNT ='COUNT'

valid_strategies = [SUM, TIMESERIES, COUNT, SUM_OBJECTS]

def _store_cache(key, value):
    pickled_object = pickle.dumps(value)
    red.set(key, pickled_object)
    return True

def _load_cache(key):
    cached_object = red.get(key)
    if not cached_object:
        return None
    return pickle.loads(cached_object)       

def execute_with_partial_history_cache(metric_name, query, object_model, strategy):
    # Redis object names
    CURRENT_MAX_ID = f'{g.active_organisation}_{object_model.__table__.name}_max_id_10'
    HIGHEST_ID_CACHED = f'{metric_name}_{g.active_organisation}_max_cached_id_10'
    CACHE_RESULT = f'{metric_name}_{g.active_organisation}_10'

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
    highest_id_in_cache = 0
    cache_result = _load_cache(CACHE_RESULT)
    filtered_query = query.filter(object_model.id > highest_id_in_cache)
    
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
    query_result = query.all()
    print('aaa')
    print(query_result)
    print('aaa')
    print(cache_result)
    print('aaa')
    return query_result

strategy_functions = { SUM: _sum_strategy, COUNT: _count_strategy, SUM_OBJECTS: _sum_list_of_objects }
