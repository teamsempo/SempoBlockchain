import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";

import {
  ACTIVATE_FAILURE,
  ACTIVATE_REQUEST,
  ACTIVATE_SUCCESS,
  ActivateAction,
  REGISTER_FAILURE,
  REGISTER_INACTIVE,
  REGISTER_REQUEST,
  REGISTER_SUCCESS,
  RegisterAction,
  REQUEST_RESET_FAILURE,
  REQUEST_RESET_REQUEST,
  REQUEST_RESET_SUCCESS,
  RESET_PASSWORD_FAILURE,
  RESET_PASSWORD_REQUEST,
  RESET_PASSWORD_SUCCESS,
  ResetEmailAction,
  ResetPasswordAction,
  INVITE_USER_FAILURE,
  INVITE_USER_REQUEST,
  INVITE_USER_SUCCESS,
  InviteUserAction,
  UPDATE_INVITE_USER_LIST,
  DEEP_UPDATE_INVITE_USER_LIST,
  Invite,
  InviteUserListAction,
  UPDATE_ADMIN_USER_LIST,
  DELETE_INVITE_REQUEST,
  DELETE_INVITE_SUCCESS,
  DELETE_INVITE_FAILURE,
  DeleteInviteAction,
  EDIT_ADMIN_USER_FAILURE,
  EDIT_ADMIN_USER_REQUEST,
  EDIT_ADMIN_USER_SUCCESS,
  UpdateUserAction,
  LOAD_ADMIN_USER_FAILURE,
  LOAD_ADMIN_USER_REQUEST,
  LOAD_ADMIN_USER_SUCCESS,
  AdminUser,
  AdminUserListAction,
  UserListAction,
  VALIDATE_TFA_FAILURE,
  VALIDATE_TFA_REQUEST,
  VALIDATE_TFA_SUCCESS,
  ValidateTfaAction
} from "./types";

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

export const register = (state = initialState, action: RegisterAction) => {
  switch (action.type) {
    case REGISTER_REQUEST:
      return { ...state, isRequesting: true };
    case REGISTER_SUCCESS:
      return { ...state, isRequesting: false, registerSuccess: true };
    case REGISTER_FAILURE:
      return {
        ...state,
        isRequesting: false,
        registerSuccess: false,
        error: action.error || "unknown error"
      };
    case REGISTER_INACTIVE:
      return initialState;
    default:
      return state;
  }
};

export const activate = (state = initialState, action: ActivateAction) => {
  switch (action.type) {
    case ACTIVATE_REQUEST:
      return { ...state, isRequesting: true };
    case ACTIVATE_SUCCESS:
      return { ...state, isRequesting: false, activateSuccess: true };
    case ACTIVATE_FAILURE:
      return {
        ...state,
        isRequesting: false,
        activateSuccess: false,
        error: action.error || "unknown error"
      };
    default:
      return state;
  }
};

export const requestResetEmailState = (
  state = initialState,
  action: ResetEmailAction
) => {
  switch (action.type) {
    case REQUEST_RESET_REQUEST:
      return { ...state, isRequesting: true };
    case REQUEST_RESET_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case REQUEST_RESET_FAILURE:
      return {
        ...state,
        isRequesting: false,
        success: false,
        error: action.error || "unknown error"
      };
    default:
      return state;
  }
};

export const resetPasswordState = (
  state = initialState,
  action: ResetPasswordAction
) => {
  switch (action.type) {
    case RESET_PASSWORD_REQUEST:
      return { ...state, isRequesting: true };
    case RESET_PASSWORD_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case RESET_PASSWORD_FAILURE:
      return {
        ...state,
        isRequesting: false,
        success: false,
        error: action.error || "unknown error"
      };
    default:
      return state;
  }
};

const adminsById = (
  state: AdminUser[] = [] || {},
  action: AdminUserListAction
): AdminUser[] => {
  switch (action.type) {
    case UPDATE_ADMIN_USER_LIST:
      return DEEEEEEP(state, action.admins);
    default:
      return state;
  }
};

const invitesById = (
  state: Invite[] = [] || {},
  action: InviteUserListAction
): Invite[] => {
  switch (action.type) {
    case DEEP_UPDATE_INVITE_USER_LIST:
      if (action.invites) return DEEEEEEP(state, action.invites) || state;
      else return state;
    case UPDATE_INVITE_USER_LIST:
      return action.invites;
    default:
      return state;
  }
};

interface UserListState {
  isRequesting: boolean;
  success: boolean;
  error: null | string;
}

const initialLoadStatusState: UserListState = {
  isRequesting: false,
  success: false,
  error: null
};

export const loadStatus = (
  state = initialLoadStatusState,
  action: UserListAction
) => {
  switch (action.type) {
    case LOAD_ADMIN_USER_REQUEST:
      return { ...state, isRequesting: true };
    case LOAD_ADMIN_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case LOAD_ADMIN_USER_FAILURE:
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

export const editStatus = (state = initialState, action: UpdateUserAction) => {
  switch (action.type) {
    case EDIT_ADMIN_USER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case EDIT_ADMIN_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case EDIT_ADMIN_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const createStatus = (
  state = initialState,
  action: InviteUserAction
) => {
  switch (action.type) {
    case INVITE_USER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case INVITE_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case INVITE_USER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const deleteStatus = (
  state = initialState,
  action: DeleteInviteAction
) => {
  switch (action.type) {
    case DELETE_INVITE_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case DELETE_INVITE_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case DELETE_INVITE_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const adminUsers = combineReducers({
  adminsById,
  invitesById,
  loadStatus,
  editStatus,
  createStatus,
  deleteStatus
});

export const validateTFA = (
  state = initialState,
  action: ValidateTfaAction
) => {
  switch (action.type) {
    case VALIDATE_TFA_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case VALIDATE_TFA_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case VALIDATE_TFA_FAILURE:
      return {
        ...state,
        isRequesting: false,
        error: action.error || "unknown error"
      };
    default:
      return state;
  }
};
