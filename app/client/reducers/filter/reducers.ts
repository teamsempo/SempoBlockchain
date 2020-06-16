import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";

import {
  FilterListActionTypes,
  LoadFilterActionTypes,
  CreateFilterActionTypes
} from "./types";
import {
  FilterListAction,
  LoadFilterAction,
  CreateFilterAction
} from "./actions";

const byId = (state = {}, action: FilterListAction) => {
  switch (action.type) {
    case FilterListActionTypes.UPDATE_FILTER_LIST:
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
  error: null,
  success: false
};

const loadStatus = (state = initialState, action: LoadFilterAction) => {
  switch (action.type) {
    case LoadFilterActionTypes.LOAD_FILTERS_REQUEST:
      return { ...state, isRequesting: true };

    case LoadFilterActionTypes.LOAD_FILTERS_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LoadFilterActionTypes.LOAD_FILTERS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const createStatus = (state = initialState, action: CreateFilterAction) => {
  switch (action.type) {
    case CreateFilterActionTypes.RESET_CREATE_FILTER:
      return initialState;

    case CreateFilterActionTypes.CREATE_FILTER_REQUEST:
      return { ...state, isRequesting: true };

    case CreateFilterActionTypes.CREATE_FILTER_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case CreateFilterActionTypes.CREATE_FILTER_FAILURE:
      return {
        ...state,
        isRequesting: false,
        success: false,
        error: action.error
      };

    default:
      return state;
  }
};

export const filters = combineReducers({
  byId,
  loadStatus,
  createStatus
});
