import { combineReducers } from "redux";

import {
  UserByIDs,
  UserListActionTypes,
  CreateUserActionTypes,
  LoadUserActionTypes,
  EditUserActionTypes,
  DeleteUserActionTypes,
  ResetPinActionTypes,
  LoadUserHistoryActionTypes
} from "./types";
import {
  UserListAction,
  CreateUserAction,
  EditUserAction,
  LoadUserAction,
  DeleteUserAction,
  ResetPinAction,
  LoadUserHistoryAction
} from "./actions";

import { DEEEEEEP } from "../../utils";

const byId = (state: UserByIDs = {}, action: UserListAction) => {
  switch (action.type) {
    case UserListActionTypes.REPLACE_USER_LIST:
      return action.payload;
    case UserListActionTypes.UPDATE_USER_LIST:
      return { ...state, ...action.payload };
    case UserListActionTypes.DEEP_UPDATE_USER_LIST:
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

const loadStatus = (state = initialState, action: LoadUserAction) => {
  switch (action.type) {
    case LoadUserActionTypes.LOAD_USER_REQUEST:
      return { ...state, isRequesting: true };

    case LoadUserActionTypes.LOAD_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LoadUserActionTypes.LOAD_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const editStatus = (state = initialState, action: EditUserAction) => {
  switch (action.type) {
    case EditUserActionTypes.EDIT_USER_REQUEST:
      return { ...state, isRequesting: true };

    case EditUserActionTypes.EDIT_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case EditUserActionTypes.EDIT_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const deleteStatus = (state = initialState, action: DeleteUserAction) => {
  switch (action.type) {
    case DeleteUserActionTypes.DELETE_USER_REQUEST:
      return { ...state, isRequesting: true };
    case DeleteUserActionTypes.DELETE_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case DeleteUserActionTypes.DELETE_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const pinStatus = (state = initialState, action: ResetPinAction) => {
  switch (action.type) {
    case ResetPinActionTypes.RESET_PIN_REQUEST:
      return { ...state, isRequesting: true };

    case ResetPinActionTypes.RESET_PIN_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case ResetPinActionTypes.RESET_PIN_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

interface CreateUserState {
  isRequesting: boolean;
  error: null | string;
  success: boolean;
  one_time_code: null | undefined | string;
}

const initialCreateStatusState: CreateUserState = {
  isRequesting: false,
  error: null,
  success: false,
  one_time_code: null
};

const createStatus = (
  state = initialCreateStatusState,
  action: CreateUserAction
) => {
  switch (action.type) {
    case CreateUserActionTypes.RESET_CREATE_USER:
      return initialCreateStatusState;

    case CreateUserActionTypes.CREATE_USER_REQUEST:
      return { ...state, isRequesting: true };

    case CreateUserActionTypes.CREATE_USER_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        success: true,
        one_time_code: action.payload.data.user.one_time_code
      };

    case CreateUserActionTypes.CREATE_USER_FAILURE:
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

interface LoadHistoryStatusState {
  isRequesting: boolean;
  error?: Error | null | string;
  success: Boolean;
  changes: any;
  visible: boolean;
}

const initialLoadHistoryStatusState: LoadHistoryStatusState = {
  isRequesting: false,
  error: null,
  success: false,
  changes: [],
  visible: false
};

const loadHistory = (
  state = initialLoadHistoryStatusState,
  action: LoadUserHistoryAction
) => {
  switch (action.type) {
    case LoadUserHistoryActionTypes.LOAD_USER_HISTORY_REQUEST:
      return { ...state, isRequesting: true };

    case LoadUserHistoryActionTypes.LOAD_USER_HISTORY_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        success: true,
        changes: action.payload
      };

    case LoadUserHistoryActionTypes.LOAD_USER_HISTORY_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};
export const users = combineReducers({
  byId,
  loadStatus,
  editStatus,
  deleteStatus,
  createStatus,
  pinStatus,
  loadHistory
});
