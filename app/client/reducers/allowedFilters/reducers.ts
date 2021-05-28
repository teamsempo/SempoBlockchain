import { combineReducers, ReducersMapObject } from "redux";
import { DEEEEEEP } from "../../utils";

import { AllowedFiltersAction } from "./actions";
import { AllowedFiltersActionTypes } from "./types";

const allowedFilterState = (state = {}, action: AllowedFiltersAction) => {
  switch (action.type) {
    case AllowedFiltersActionTypes.UPDATE_ALLOWED_FILTERS:
      return DEEEEEEP(state, action.payload);
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
  error: null
};

const loadStatus = (state = initialState, action: AllowedFiltersAction) => {
  switch (action.type) {
    case AllowedFiltersActionTypes.LOAD_ALLOWED_FILTERS_REQUEST:
      return { ...state, isRequesting: true };

    case AllowedFiltersActionTypes.LOAD_ALLOWED_FILTERS_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case AllowedFiltersActionTypes.LOAD_ALLOWED_FILTERS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

function createNamedWrapperReducer(reducerFunction: any, reducerName: string) {
  return (state: any, action: any) => {
    const { name } = action;
    const isInitializationCall = state === undefined;
    if (name !== reducerName && !isInitializationCall) return state;

    return reducerFunction(state, action);
  };
}

const user = combineReducers({
  loadStatus: createNamedWrapperReducer(loadStatus, "user"),
  allowed: createNamedWrapperReducer(allowedFilterState, "user")
});

const credit_transfer = combineReducers({
  loadStatus: createNamedWrapperReducer(loadStatus, "credit_transfer"),
  allowed: createNamedWrapperReducer(allowedFilterState, "credit_transfer")
});

const combined: ReducersMapObject = {
  user,
  credit_transfer //Follows underscore convention to match python
};

export const allowedFilters = combineReducers(combined);
