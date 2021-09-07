from server import red, db
from flask import g
import pickle
import config
import datetime
from server.utils.executor import standard_executor_job

SUM = 'SUM'
TALLY = 'TALLY'
SUM_OBJECTS ='SUM_OBJECTS'
COUNT ='COUNT'
FIRST_COUNT = 'FIRST_COUNT'
QUERY_ALL = 'QUERY_ALL'

valid_strategies = [SUM, TALLY, COUNT, SUM_OBJECTS, FIRST_COUNT, QUERY_ALL]
# Combinatory stategies which aren't cachable
dumb_strategies = [FIRST_COUNT, QUERY_ALL]

# Workaround for an incongruity between flask-sqlalchemy and sqlalchemy
def dummy_function():
    return True
db.session._autoflush = dummy_function

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

def get_first_day(date_filter_attribute, enable_cache = True):
    # We need to get the first day data exists for every table, in order to calculate percentage-changes
    # This is a rather expensive operation, but the result is always the same so we can cache it! 
    if enable_cache:
        if g.get('query_organisations'):
            ORG_STRING = get_metrics_org_string(g.query_organisations)
        else:
            ORG_STRING = get_metrics_org_string(g.active_organisation.id)
        FIRST_DAY = f'{ORG_STRING}_FIRST_DAY_{str(date_filter_attribute)}'
        result = _load_cache(FIRST_DAY)
        if result:
            return result
    today = datetime.datetime.now().replace(minute=0, hour=0, second=0, microsecond=0)
    first_day = db.session.query(db.func.min(date_filter_attribute)).scalar() or today
    if first_day and enable_cache:
        _store_cache(FIRST_DAY, first_day)
    return first_day or today

def execute_with_partial_history_cache(metric_name, query, object_model, strategy, enable_cache = True, group_by=None, query_name=''):
    # enable_cache pass-thru. This is so we don't cache data when filters are active.
    if strategy in dumb_strategies or not enable_cache:
        return _handle_combinatory_strategy(query, None, strategy)
    if query_name:
        metric_name = metric_name + '_' + query_name
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
        query_max = db.session.query(db.func.max(object_model.id)).with_session(db.session).first()
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

def rebuild_metrics_cache():
    @standard_executor_job
    def _async_rebuild_metrics_cache():
        from server.utils.metrics.metrics import calculate_transfer_stats
        calculate_transfer_stats(None, None, None, 'credit_transfer', 'all', False, 'day', 'ungrouped', None)
        calculate_transfer_stats(None, None, None, 'user', 'all', False, 'day', 'ungrouped', None)
    _async_rebuild_metrics_cache.submit()

def _handle_combinatory_strategy(query, cache_result, strategy):
    return strategy_functions[strategy](query, cache_result)

def _sum_strategy(query, cache_result):
    return float(query.with_session(db.session).first().total or 0) + (cache_result or 0)


def _tally_strategy(query, cache_result):
    a = query.with_session(db.session).all()[0][0]
    if not cache_result:
        cache_result = [[0]]
    return [[float(a or 0) + cache_result[0][0]]]

def _count_strategy(query, cache_result):
    return query.with_session(db.session).count() + (cache_result or 0)

def _sum_list_of_objects(query, cache_result):
    combined_results = {}
    for r in cache_result or []:
        if r[0]:
            if len(r) == 3:
                combined_results[(r[1], r[2])] = r[0]
            else:
                combined_results[(r[1])] = r[0]

    query_result = query.with_session(db.session).all()
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
    return query.with_session(db.session).first().count

def _return_all(query, cache_result):
    return query.with_session(db.session).all()

strategy_functions = { SUM: _sum_strategy, TALLY: _tally_strategy,  COUNT: _count_strategy, SUM_OBJECTS: _sum_list_of_objects, FIRST_COUNT: _first_count, QUERY_ALL: _return_all }
