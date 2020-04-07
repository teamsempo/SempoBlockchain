import { combineReducers } from "redux";
import { DEEEEEEP } from "../utils";

export const DEEP_UPDATE_USER_LIST = "DEEP_UPDATE_USER_LIST";
export const UPDATE_USER_LIST = "UPDATE_USER_LIST";

export const LOAD_USER_REQUEST = "LOAD_USER_REQUEST";
export const LOAD_USER_SUCCESS = "LOAD_USER_SUCCESS";
export const LOAD_USER_FAILURE = "LOAD_USER_FAILURE";

export const EDIT_USER_REQUEST = "EDIT_USER_REQUEST";
export const EDIT_USER_SUCCESS = "EDIT_USER_SUCCESS";
export const EDIT_USER_FAILURE = "EDIT_USER_FAILURE";

export const RESET_PIN_REQUEST = "RESET_PIN_REQUEST";
export const RESET_PIN_SUCCESS = "RESET_PIN_SUCCESS";
export const RESET_PIN_FAILURE = "RESET_PIN_FAILURE";

export const CREATE_USER_REQUEST = "CREATE_USER_REQUEST";
export const CREATE_USER_SUCCESS = "CREATE_USER_SUCCESS";
export const CREATE_USER_FAILURE = "CREATE_USER_FAILURE";

export const DELETE_USER_REQUEST = "DELETE_USER_REQUEST";
export const DELETE_USER_SUCCESS = "DELETE_USER_SUCCESS";
export const DELETE_USER_FAILURE = "DELETE_USER_FAILURE";

export const RESET_CREATE_USER = "RESET_CREATE_USER";

const byId = (state = {}, action) => {
  switch (action.type) {
    case DEEP_UPDATE_USER_LIST:
      return DEEEEEEP(state, action.users);

    case UPDATE_USER_LIST:
      return action.users;

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
    case LOAD_USER_REQUEST:
      return { ...state, isRequesting: true };

    case LOAD_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LOAD_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialEditStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const editStatus = (state = initialEditStatusState, action) => {
  switch (action.type) {
    case EDIT_USER_REQUEST:
      return { ...state, isRequesting: true };

    case EDIT_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case EDIT_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialDeleteStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const deleteStatus = (state = initialDeleteStatusState, action) => {
  switch (action.type) {
    case DELETE_USER_REQUEST:
      return { ...state, isRequesting: true };
    case DELETE_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case DELETE_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const initialPinStatus = {
  isRequesting: false,
  error: null,
  success: false
};
const pinStatus = (state = initialPinStatus, action) => {
  switch (action.type) {
    case RESET_PIN_REQUEST:
      return { ...state, isRequesting: true };

    case RESET_PIN_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case RESET_PIN_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialCreateStatusState = {
  isRequesting: false,
  error: null,
  success: false,
  one_time_code: null
};

const createStatus = (state = initialCreateStatusState, action) => {
  switch (action.type) {
    case RESET_CREATE_USER:
      return initialCreateStatusState;

    case CREATE_USER_REQUEST:
      return { ...state, isRequesting: true };

    case CREATE_USER_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        success: true,
        one_time_code: action.result.data.user.one_time_code,
        //TODO: Fix this to actually determine if private key is present
        has_private_key: true
      };

    case CREATE_USER_FAILURE:
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

export const users = combineReducers({
  byId,
  loadStatus,
  editStatus,
  deleteStatus,
  createStatus,
  pinStatus
});

// ACTIONS
export const loadUser = payload => ({
  type: LOAD_USER_REQUEST,
  payload
});

export const editUser = payload => ({
  type: EDIT_USER_REQUEST,
  payload
});

export const deleteUser = payload => ({
  type: DELETE_USER_REQUEST,
  payload
});

export const resetPin = payload => ({
  type: RESET_PIN_REQUEST,
  payload
});

export const createUser = payload => ({
  type: CREATE_USER_REQUEST,
  payload
});
