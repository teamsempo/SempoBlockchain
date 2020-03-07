import {
  ACTIVATE_REQUEST,
  ActivatePayload,
  INVITE_USER_REQUEST,
  InviteUserPayload,
  LoginRequestPayload,
  REGISTER_FAILURE,
  REGISTER_INACTIVE,
  REGISTER_REQUEST,
  REGISTER_SUCCESS,
  RegisterRequestPayload,
  REQUEST_RESET_REQUEST,
  ResetEmailPayload,
  RESET_PASSWORD_REQUEST,
  ResetPasswordPayload,
  EDIT_ADMIN_USER_REQUEST,
  UpdateActiveOrgPayload,
  UpdateUserPayload,
  LOAD_ADMIN_USER_REQUEST,
  VALIDATE_TFA_REQUEST,
  ValidateTfaPayload,
  DELETE_INVITE_REQUEST,
  DeleteInvitePayload,
  LoginSuccessPayload,
  LoginActionTypes,
  LoginPartialPayload
} from "./types";

import { createAction, ActionsUnion } from "../../reduxUtils";

export const updateActiveOrgRequest = (payload: UpdateActiveOrgPayload) =>
  createAction(LoginActionTypes.UPDATE_ACTIVE_ORG, payload);
export const reauthRequest = () =>
  createAction(LoginActionTypes.REAUTH_REQUEST);
export const loginRequest = (payload: LoginRequestPayload) =>
  createAction(LoginActionTypes.LOGIN_REQUEST, payload);
export const loginPartial = (payload: LoginPartialPayload) =>
  createAction(LoginActionTypes.LOGIN_PARTIAL, payload);
export const loginSuccess = (payload: LoginSuccessPayload) =>
  createAction(LoginActionTypes.LOGIN_SUCCESS, payload);
export const loginFailure = (error: string) =>
  createAction(LoginActionTypes.LOGIN_FAILURE, error);
export const logout = () => createAction(LoginActionTypes.LOGOUT);

export const LoginActions = {
  updateActiveOrgRequest,
  reauthRequest,
  loginRequest,
  loginPartial,
  loginSuccess,
  loginFailure,
  logout
};

// type declaration merging with above
export type LoginActions = ActionsUnion<typeof LoginActions>;

export const registerRequest = (payload: RegisterRequestPayload) =>
  createAction(REGISTER_REQUEST, payload);
export const registerSuccess = () => createAction(REGISTER_SUCCESS);
export const registerFailure = (error: string) =>
  createAction(REGISTER_FAILURE, error);
export const deactivateRegister = () => createAction(REGISTER_INACTIVE);
export const activateAccount = (payload: ActivatePayload) =>
  createAction(ACTIVATE_REQUEST, payload);
export const requestPasswordResetEmail = (payload: ResetEmailPayload) =>
  createAction(REQUEST_RESET_REQUEST, payload);
export const resetPassword = (payload: ResetPasswordPayload) =>
  createAction(RESET_PASSWORD_REQUEST, payload);
export const loadUserList = () => createAction(LOAD_ADMIN_USER_REQUEST);
export const updateUser = (payload: UpdateUserPayload) =>
  createAction(EDIT_ADMIN_USER_REQUEST, payload);
export const inviteUser = (payload: InviteUserPayload) =>
  createAction(INVITE_USER_REQUEST, payload);
export const deleteInvite = (payload: DeleteInvitePayload) =>
  createAction(DELETE_INVITE_REQUEST, payload);
export const validateTFARequest = (payload: ValidateTfaPayload) =>
  createAction(VALIDATE_TFA_REQUEST, payload);
