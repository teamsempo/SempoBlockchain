import { combineReducers } from 'redux';
import { DEEEEEEP } from '../utils';

export const LOAD_METRICS_REQUEST = 'LOAD_METRICS_REQUEST';
export const LOAD_METRICS_SUCCESS = 'LOAD_METRICS_SUCCESS';
export const LOAD_METRICS_ERROR = 'LOAD_METRICS_ERROR';
export const UPDATE_METRICS = 'UPDATE_METRICS';

const metricsState = (state = {}, action) => {
  switch (action.type) {
    case UPDATE_METRICS:
      return DEEEEEEP(state, action.metrics);
    default:
      return state;
  }
};

const initialLoadMetricsState = {
  isRequesting: false,
  error: null,
  success: false,
};

const loadStatus = (state = initialLoadMetricsState, action) => {
  switch (action.type) {
    case LOAD_METRICS_REQUEST:
      return { ...state, isRequesting: true };
    case LOAD_METRICS_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case LOAD_METRICS_ERROR:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const metrics = combineReducers({
  metricsState,
  loadStatus,
});

export const loadMetrics = payload => ({
  type: LOAD_METRICS_REQUEST,
  payload,
});
