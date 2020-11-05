# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

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
