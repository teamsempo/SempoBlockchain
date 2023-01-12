import { combineReducers } from "redux";

import { LoadMetricAction, MetricAction } from "./actions";
import { MetricsActionType, LoadMetricsActionType, Metrics } from "./types";

const metricsState = (state: Metrics[] = [] || {}, action: MetricAction) => {
  switch (action.type) {
    case MetricsActionType.UPDATE_METRICS:
      //Shallow merge so that aggregates don't compound
      return { ...state, ...action.payload };
    default:
      return state;
  }
};

interface RequestingState {
  isRequesting: boolean;
  success: boolean;
  error: null | string;
}

const initialState: RequestingState = {
  isRequesting: false,
  success: false,
  error: null,
};

const loadStatus = (state = initialState, action: LoadMetricAction) => {
  switch (action.type) {
    case LoadMetricsActionType.LOAD_METRICS_REQUEST:
      return { ...state, isRequesting: true };
    case LoadMetricsActionType.LOAD_METRICS_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case LoadMetricsActionType.LOAD_METRICS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const metrics = combineReducers({
  metricsState,
  loadStatus,
});
