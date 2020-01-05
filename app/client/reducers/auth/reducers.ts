import {
  ACTIVATE_FAILURE,
  ACTIVATE_REQUEST,
  ACTIVATE_SUCCESS, ActivateAction, INVITE_USER_FAILURE, INVITE_USER_REQUEST, INVITE_USER_SUCCESS, InviteUserAction,
  REGISTER_FAILURE,
  REGISTER_INACTIVE,
  REGISTER_REQUEST,
  REGISTER_SUCCESS, RegisterAction,
  REQUEST_RESET_FAILURE,
  REQUEST_RESET_REQUEST,
  REQUEST_RESET_SUCCESS,
  RESET_PASSWORD_FAILURE,
  RESET_PASSWORD_REQUEST,
  RESET_PASSWORD_SUCCESS, ResetEmailAction, ResetPasswordAction,
  UPDATE_USER_FAILURE,
  UPDATE_USER_REQUEST,
  UPDATE_USER_SUCCESS, UpdateUserAction,
  USER_LIST_FAILURE,
  USER_LIST_REQUEST,
  USER_LIST_SUCCESS, UserListAction, VALIDATE_TFA_FAILURE, VALIDATE_TFA_REQUEST, VALIDATE_TFA_SUCCESS, ValidateTfaAction
} from "./types";

interface RequestingState {
  isRequesting: boolean,
  success: boolean,
  error: null | string
}

const initialState: RequestingState = {
  isRequesting: false,
  success: false,
  error: null
};

export const register = (state = initialState, action: RegisterAction) => {
  switch (action.type) {
    case REGISTER_REQUEST:
      return {...state, isRequesting: true};
    case REGISTER_SUCCESS:
      return {...state, isRequesting: false, registerSuccess: true};
    case REGISTER_FAILURE:
      return {...state, isRequesting: false, registerSuccess: false, error: action.error || 'unknown error'};
    case REGISTER_INACTIVE:
      return initialState;
    default:
      return state;
  }
};

export const activate = (state = initialState, action: ActivateAction) => {
  switch (action.type) {
    case ACTIVATE_REQUEST:
      return {...state, isRequesting: true};
    case ACTIVATE_SUCCESS:
      return {...state, isRequesting: false, activateSuccess: true};
    case ACTIVATE_FAILURE:
      return {...state, isRequesting: false, activateSuccess: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

export const requestResetEmailState = (state = initialState, action: ResetEmailAction) => {
  switch (action.type) {
    case REQUEST_RESET_REQUEST:
      return {...state, isRequesting: true};
    case REQUEST_RESET_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case REQUEST_RESET_FAILURE:
      return {...state, isRequesting: false, success: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

export const resetPasswordState = (state = initialState, action: ResetPasswordAction) => {
  switch (action.type) {
    case RESET_PASSWORD_REQUEST:
      return {...state, isRequesting: true};
    case RESET_PASSWORD_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case RESET_PASSWORD_FAILURE:
      return {...state, isRequesting: false, success: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

//TODO(refactor): what is userList data actually?
interface UserListState {
  isRequesting: boolean,
  success: boolean,
  error: null | string,
  userList: string[]
}

const initialUserListState: UserListState = {
  isRequesting: false,
  success: false,
  error: null,
  userList: []
};

export const userList = (state = initialUserListState, action: UserListAction) => {
  switch (action.type) {
    case USER_LIST_REQUEST:
      return {...state, isRequesting: true};
    case USER_LIST_SUCCESS:
      return {...state, isRequesting: false, success: true, userList: action.load_result.admin_list,};
    case USER_LIST_FAILURE:
      return {...state, isRequesting: false, success: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

export const updateUserRequest = (state = initialState, action: UpdateUserAction) => {
    switch (action.type) {
        case UPDATE_USER_REQUEST:
            return {...state, isRequesting: true, error: null, success: false};
        case UPDATE_USER_SUCCESS:
            return {...state, isRequesting: false, success: true};
        case UPDATE_USER_FAILURE:
            return {...state, isRequesting: false, error: action.error || 'unknown error'};
        default:
            return state;
    }
};

export const inviteUserRequest = (state = initialState, action: InviteUserAction) => {
    switch (action.type) {
        case INVITE_USER_REQUEST:
            return {...state, isRequesting: true, error: null, success: false};
        case INVITE_USER_SUCCESS:
            return {...state, isRequesting: false, success: true};
        case INVITE_USER_FAILURE:
            return {...state, isRequesting: false, error: action.error || 'unknown error'};
        default:
            return state;
    }
};

export const validateTFA = (state = initialState, action: ValidateTfaAction) => {
    switch (action.type) {
        case VALIDATE_TFA_REQUEST:
            return {...state, isRequesting: true, error: null, success: false};
        case VALIDATE_TFA_SUCCESS:
            return {...state, isRequesting: false, success: true};
        case VALIDATE_TFA_FAILURE:
            return {...state, isRequesting: false, error: action.error || 'unknown error'};
        default:
            return state;
    }
};

