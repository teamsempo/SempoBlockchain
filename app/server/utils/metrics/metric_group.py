class MetricGroup(object):
   
    def __init__(self,
                timeseries_unit = 'day',
                metrics = None,
                filterable_attributes = None,
                timezone = None):
        timeseries_unit = timeseries_unit
        metrics = metrics or []
        filterable_attributes = filterable_attributes or []
        timezone = timezone
