import { combineReducers } from "redux";

import { LoadAsyncAction, AsyncAction } from "./actions";
import { AsyncActionType, LoadAsyncActionType, AsyncData } from "./types";

const asyncState = (state: AsyncData[] = [] || {}, action: AsyncAction) => {
  switch (action.type) {
    case AsyncActionType.UPDATE_ASYNC:
      return { ...action.payload };
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

const loadStatus = (state = initialState, action: LoadAsyncAction) => {
  switch (action.type) {
    case LoadAsyncActionType.LOAD_ASYNC_REQUEST:
      return { ...state, isRequesting: true };
    case LoadAsyncActionType.LOAD_ASYNC_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case LoadAsyncActionType.LOAD_ASYNC_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const AsyncReducer = combineReducers({
  asyncState,
  loadStatus,
});
