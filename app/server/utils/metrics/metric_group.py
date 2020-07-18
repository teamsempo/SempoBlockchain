class MetricGroup(object):
    timeseries_unit = 'day',
    metrics = [],
    filterable_attributes = []
    
    def __init__(self,
                timeseries_unit,
                metrics,
                filterable_attributes):
        timeseries_unit = timeseries_unit
        metrics = metrics
        filterable_attributes = filterable_attributes

