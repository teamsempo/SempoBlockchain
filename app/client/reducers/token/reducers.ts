import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";

import {
  TokenListActionTypes,
  LoadTokenActionTypes,
  CreateTokenActionTypes
} from "./types";
import { TokenListAction, LoadTokenAction, CreateTokenAction } from "./actions";

const byId = (state = {}, action: TokenListAction) => {
  switch (action.type) {
    case TokenListActionTypes.UPDATE_TOKEN_LIST:
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

const loadStatus = (state = initialState, action: LoadTokenAction) => {
  switch (action.type) {
    case LoadTokenActionTypes.LOAD_TOKENS_REQUEST:
      return { ...state, isRequesting: true };

    case LoadTokenActionTypes.LOAD_TOKENS_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LoadTokenActionTypes.LOAD_TOKENS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const createStatus = (state = initialState, action: CreateTokenAction) => {
  switch (action.type) {
    case CreateTokenActionTypes.RESET_CREATE_TOKEN:
      return initialState;

    case CreateTokenActionTypes.CREATE_TOKEN_REQUEST:
      return { ...state, isRequesting: true };

    case CreateTokenActionTypes.CREATE_TOKEN_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case CreateTokenActionTypes.CREATE_TOKEN_FAILURE:
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

export const tokens = combineReducers({
  byId,
  loadStatus,
  createStatus
});
