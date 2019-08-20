import { combineReducers } from 'redux';
import { DEEEEEEP } from "../utils";

export const UPDATE_FILTER_LIST = "UPDATE_FILTER_LIST";

export const LOAD_FILTERS_REQUEST = "LOAD_FILTERS_REQUEST";
export const LOAD_FILTERS_SUCCESS = "LOAD_FILTERS_SUCCESS";
export const LOAD_FILTERS_FAILURE = "LOAD_FILTERS_FAILURE";

export const CREATE_FILTER_REQUEST = "CREATE_FILTER_REQUEST";
export const CREATE_FILTER_SUCCESS = "CREATE_FILTER_SUCCESS";
export const CREATE_FILTER_FAILURE = "CREATE_FILTER_FAILURE";

export const RESET_CREATE_FILTER = "RESET_CREATE_FILTER";

const byId = (state = {}, action) => {
  switch (action.type) {
    case UPDATE_FILTER_LIST:
      return DEEEEEEP(state, action.filters);

    default:
      return state;
  }
};

const initialLoadStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const loadStatus = (state = initialLoadStatusState, action) => {
  switch (action.type) {
    case LOAD_FILTERS_REQUEST:
      return {...state, isRequesting: true};

    case LOAD_FILTERS_SUCCESS:
      return {...state, isRequesting: false, success: true};

    case LOAD_FILTERS_FAILURE:
      return {...state, isRequesting: false, error: action.error};

    default:
      return state;
  }
};

const initialCreateStatusState = {
  isRequesting: false,
  error: null,
  success: false,
};

const createStatus = (state = initialCreateStatusState, action) => {
  switch (action.type) {
    case RESET_CREATE_FILTER:
      return initialCreateStatusState;

    case CREATE_FILTER_REQUEST:
      return {...state, isRequesting: true};

    case CREATE_FILTER_SUCCESS:
      return {...state, isRequesting: false, success: true};

    case CREATE_FILTER_FAILURE:
      return {...state, isRequesting: false, success: false, error: action.error};

    default:
      return state;
  }
};


export const filters = combineReducers({
    byId,
    loadStatus,
    createStatus
});


// ACTIONS
export const loadFilters = (payload) => (
  {
    type: LOAD_FILTERS_REQUEST,
    payload,
  }
);

export const createFilter = (payload) => (
  {
    type: CREATE_FILTER_REQUEST,
    payload,
  }
);
