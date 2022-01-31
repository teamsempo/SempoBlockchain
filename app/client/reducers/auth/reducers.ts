import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";

import {
  UPDATE_ADMIN_USER_LIST,
  RegisterActionTypes,
  ActivateActionTypes,
  ResetPasswordEmailActionTypes,
  ResetPasswordActionTypes,
  InviteUserListActionTypes,
  LoadAdminUserListActionTypes,
  EditAdminUserActionTypes,
  InviteUserActionTypes,
  DeleteInviteActionTypes,
  AdminResetPasswordActionTypes,
  ValidateTfaActionTypes,
  InviteByIDs,
  AdminUserByIDs,
} from "./types";

import {
  RegisterAction,
  ActivateAccountAction,
  ResetPasswordEmailAction,
  ResetPasswordAction,
  AdminUserListAction,
  InviteUserListAction,
  LoadAdminUserListAction,
  EditAdminUserAction,
  InviteUserAction,
  DeleteInviteAction,
  AdminResetPasswordAction,
  ValidateTfaAction,
} from "./actions";

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

export const register = (state = initialState, action: RegisterAction) => {
  switch (action.type) {
    case RegisterActionTypes.REGISTER_REQUEST:
      return { ...state, isRequesting: true };
    case RegisterActionTypes.REGISTER_SUCCESS:
      return { ...state, isRequesting: false, registerSuccess: true };
    case RegisterActionTypes.REGISTER_FAILURE:
      return {
        ...state,
        isRequesting: false,
        registerSuccess: false,
        error: action.error || "unknown error",
      };
    case RegisterActionTypes.REGISTER_INACTIVE:
      return initialState;
    default:
      return state;
  }
};

export const activate = (
  state = initialState,
  action: ActivateAccountAction
) => {
  switch (action.type) {
    case ActivateActionTypes.ACTIVATE_REQUEST:
      return { ...state, isRequesting: true };
    case ActivateActionTypes.ACTIVATE_SUCCESS:
      return { ...state, isRequesting: false, activateSuccess: true };
    case ActivateActionTypes.ACTIVATE_FAILURE:
      return {
        ...state,
        isRequesting: false,
        activateSuccess: false,
        error: action.error || "unknown error",
      };
    default:
      return state;
  }
};

export const requestResetEmailState = (
  state = initialState,
  action: ResetPasswordEmailAction
) => {
  switch (action.type) {
    case ResetPasswordEmailActionTypes.REQUEST_RESET_REQUEST:
      return { ...state, isRequesting: true };
    case ResetPasswordEmailActionTypes.REQUEST_RESET_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case ResetPasswordEmailActionTypes.REQUEST_RESET_FAILURE:
      return {
        ...state,
        isRequesting: false,
        success: false,
        error: action.error || "unknown error",
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
    case ResetPasswordActionTypes.RESET_PASSWORD_REQUEST:
      return { ...state, isRequesting: true };
    case ResetPasswordActionTypes.RESET_PASSWORD_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case ResetPasswordActionTypes.RESET_PASSWORD_FAILURE:
      return {
        ...state,
        isRequesting: false,
        success: false,
        error: action.error || "unknown error",
      };
    default:
      return state;
  }
};

const adminsById = (
  state: AdminUserByIDs = {},
  action: AdminUserListAction
): AdminUserByIDs => {
  switch (action.type) {
    case UPDATE_ADMIN_USER_LIST:
      return DEEEEEEP(state, action.payload);
    default:
      return state;
  }
};

const invitesById = (
  state: InviteByIDs = {},
  action: InviteUserListAction
): InviteByIDs => {
  switch (action.type) {
    case InviteUserListActionTypes.DEEP_UPDATE_INVITE_USER_LIST:
      return DEEEEEEP(state, action.payload);
    case InviteUserListActionTypes.UPDATE_INVITE_USER_LIST:
      return action.payload;
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
  error: null,
};

export const loadStatus = (
  state = initialLoadStatusState,
  action: LoadAdminUserListAction
) => {
  switch (action.type) {
    case LoadAdminUserListActionTypes.LOAD_ADMIN_USER_REQUEST:
      return { ...state, isRequesting: true };
    case LoadAdminUserListActionTypes.LOAD_ADMIN_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case LoadAdminUserListActionTypes.LOAD_ADMIN_USER_FAILURE:
      return {
        ...state,
        isRequesting: false,
        success: false,
        error: action.error,
      };
    default:
      return state;
  }
};

export const editStatus = (
  state = initialState,
  action: EditAdminUserAction
) => {
  switch (action.type) {
    case EditAdminUserActionTypes.EDIT_ADMIN_USER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case EditAdminUserActionTypes.EDIT_ADMIN_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case EditAdminUserActionTypes.EDIT_ADMIN_USER_FAILURE:
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
    case InviteUserActionTypes.INVITE_USER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case InviteUserActionTypes.INVITE_USER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case InviteUserActionTypes.INVITE_USER_FAILURE:
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
    case DeleteInviteActionTypes.DELETE_INVITE_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case DeleteInviteActionTypes.DELETE_INVITE_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case DeleteInviteActionTypes.DELETE_INVITE_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const adminResetPasswordStatus = (
  state = initialState,
  action: AdminResetPasswordAction
) => {
  switch (action.type) {
    case AdminResetPasswordActionTypes.ADMIN_RESET_PASSWORD_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case AdminResetPasswordActionTypes.ADMIN_RESET_PASSWORD_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case AdminResetPasswordActionTypes.ADMIN_RESET_PASSWORD_FAILURE:
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
  deleteStatus,
  adminResetPasswordStatus,
});

export const validateTFA = (
  state = initialState,
  action: ValidateTfaAction
) => {
  switch (action.type) {
    case ValidateTfaActionTypes.VALIDATE_TFA_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case ValidateTfaActionTypes.VALIDATE_TFA_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case ValidateTfaActionTypes.VALIDATE_TFA_FAILURE:
      return {
        ...state,
        isRequesting: false,
        error: action.error || "unknown error",
      };
    default:
      return state;
  }
};
