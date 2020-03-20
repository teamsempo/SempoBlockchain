import { combineReducers } from 'redux';
import { DEEEEEEP } from '../utils';

export const LOAD_CREDIT_TRANSFER_FILTERS_REQUEST =
  'LOAD_CREDIT_TRANSFER_FILTERS_REQUEST';
export const LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS =
  'LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS';
export const LOAD_CREDIT_TRANSFER_FILTERS_FAILURE =
  'LOAD_CREDIT_TRANSFER_FILTERS_FAILURE';
export const UPDATE_CREDIT_TRANSFER_FILTERS = 'UPDATE_CREDIT_TRANSFER_FILTERS';

const initialLoadStatusState = {
  isRequesting: false,
  error: null,
  success: false,
};

const creditTransferFilterState = (state = {}, action) => {
  switch (action.type) {
    case UPDATE_CREDIT_TRANSFER_FILTERS:
      return DEEEEEEP(state, action.filters);
    default:
      return state;
  }
};

const loadStatus = (state = initialLoadStatusState, action) => {
  switch (action.type) {
    case LOAD_CREDIT_TRANSFER_FILTERS_REQUEST:
      return { ...state, isRequesting: true };

    case LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LOAD_CREDIT_TRANSFER_FILTERS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const creditTransferFilters = combineReducers({
  creditTransferFilterState,
  loadStatus,
});

export const loadCreditTransferFilters = payload => ({
  type: LOAD_CREDIT_TRANSFER_FILTERS_REQUEST,
  payload,
});
