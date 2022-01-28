import {
  ActivateActionTypes,
  ActivatePayload,
  InviteUserActionTypes,
  InviteUserPayload,
  LoginRequestPayload,
  RegisterActionTypes,
  RegisterRequestPayload,
  ResetPasswordEmailActionTypes,
  ResetEmailPayload,
  ResetPasswordActionTypes,
  ResetPasswordPayload,
  EditAdminUserActionTypes,
  UpdateActiveOrgPayload,
  UpdateUserPayload,
  LoadAdminUserListActionTypes,
  ValidateTfaActionTypes,
  ValidateTfaPayload,
  DeleteInviteActionTypes,
  DeleteInvitePayload,
  AdminResetPasswordActionTypes,
  AdminResetPasswordPayload,
  LoginSuccessPayload,
  LoginActionTypes,
  LoginPartialPayload,
  UPDATE_ADMIN_USER_LIST,
  AdminUserByIDs,
  InviteUserListActionTypes,
  InviteByIDs,
} from "./types";

import { createAction, ActionsUnion } from "../../reduxUtils";

export const LoginAction = {
  updateActiveOrgRequest: (payload: UpdateActiveOrgPayload) =>
    createAction(LoginActionTypes.UPDATE_ACTIVE_ORG, payload),
  reauthRequest: () => createAction(LoginActionTypes.REAUTH_REQUEST),
  loginRequest: (payload: LoginRequestPayload) =>
    createAction(LoginActionTypes.LOGIN_REQUEST, payload),
  loginPartial: (payload: LoginPartialPayload) =>
    createAction(LoginActionTypes.LOGIN_PARTIAL, payload),
  loginSuccess: (payload: LoginSuccessPayload) =>
    createAction(LoginActionTypes.LOGIN_SUCCESS, payload),
  loginFailure: (error: string) =>
    createAction(LoginActionTypes.LOGIN_FAILURE, error),
  logout: () => createAction(LoginActionTypes.LOGOUT),
  apiLogout: () => createAction(LoginActionTypes.API_LOGOUT),
};
// type declaration merging with above
export type LoginAction = ActionsUnion<typeof LoginAction>;

export const RegisterAction = {
  registerRequest: (payload: RegisterRequestPayload) =>
    createAction(RegisterActionTypes.REGISTER_REQUEST, payload),
  registerSuccess: () => createAction(RegisterActionTypes.REGISTER_SUCCESS),
  registerFailure: (error: string) =>
    createAction(RegisterActionTypes.REGISTER_FAILURE, error),
  deactivateRegister: () => createAction(RegisterActionTypes.REGISTER_INACTIVE),
};
export type RegisterAction = ActionsUnion<typeof RegisterAction>;

export const ActivateAccountAction = {
  activateAccountRequest: (payload: ActivatePayload) =>
    createAction(ActivateActionTypes.ACTIVATE_REQUEST, payload),
  activateAccountSuccess: () =>
    createAction(ActivateActionTypes.ACTIVATE_SUCCESS),
  activateAccountFailure: (error: string) =>
    createAction(ActivateActionTypes.ACTIVATE_FAILURE, error),
};
export type ActivateAccountAction = ActionsUnion<typeof ActivateAccountAction>;

export const ResetPasswordEmailAction = {
  passwordResetEmailRequest: (payload: ResetEmailPayload) =>
    createAction(ResetPasswordEmailActionTypes.REQUEST_RESET_REQUEST, payload),
  passwordResetEmailSuccess: () =>
    createAction(ResetPasswordEmailActionTypes.REQUEST_RESET_SUCCESS),
  passwordResetEmailFailure: (error: string) =>
    createAction(ResetPasswordEmailActionTypes.REQUEST_RESET_FAILURE, error),
};
export type ResetPasswordEmailAction = ActionsUnion<
  typeof ResetPasswordEmailAction
>;

export const ResetPasswordAction = {
  resetPasswordRequest: (payload: ResetPasswordPayload) =>
    createAction(ResetPasswordActionTypes.RESET_PASSWORD_REQUEST, payload),
  resetPasswordSuccess: () =>
    createAction(ResetPasswordActionTypes.RESET_PASSWORD_SUCCESS),
  resetPasswordFailure: (error: string) =>
    createAction(ResetPasswordActionTypes.RESET_PASSWORD_FAILURE, error),
};
export type ResetPasswordAction = ActionsUnion<typeof ResetPasswordAction>;

export const AdminUserListAction = {
  updateAdminUserList: (admins: AdminUserByIDs) =>
    createAction(UPDATE_ADMIN_USER_LIST, admins),
};
export type AdminUserListAction = ActionsUnion<typeof AdminUserListAction>;

export const InviteUserListAction = {
  deepUpdateInviteUsers: (invites: InviteByIDs) =>
    createAction(
      InviteUserListActionTypes.DEEP_UPDATE_INVITE_USER_LIST,
      invites
    ),
  updateInviteUsers: (invites: InviteByIDs) =>
    createAction(InviteUserListActionTypes.UPDATE_INVITE_USER_LIST, invites),
};
export type InviteUserListAction = ActionsUnion<typeof InviteUserListAction>;

export const LoadAdminUserListAction = {
  loadAdminUserListRequest: () =>
    createAction(LoadAdminUserListActionTypes.LOAD_ADMIN_USER_REQUEST),
  loadAdminUserListSuccess: () =>
    createAction(LoadAdminUserListActionTypes.LOAD_ADMIN_USER_SUCCESS),
  loadAdminUserListFailure: (error: string) =>
    createAction(LoadAdminUserListActionTypes.LOAD_ADMIN_USER_FAILURE, error),
};
export type LoadAdminUserListAction = ActionsUnion<
  typeof LoadAdminUserListAction
>;

export const EditAdminUserAction = {
  editAdminUserRequest: (payload: UpdateUserPayload) =>
    createAction(EditAdminUserActionTypes.EDIT_ADMIN_USER_REQUEST, payload),
  editAdminUserSuccess: () =>
    createAction(EditAdminUserActionTypes.EDIT_ADMIN_USER_SUCCESS),
  editAdminUserFailure: (error: string) =>
    createAction(EditAdminUserActionTypes.EDIT_ADMIN_USER_FAILURE, error),
};
export type EditAdminUserAction = ActionsUnion<typeof EditAdminUserAction>;

export const InviteUserAction = {
  inviteUserRequest: (payload: InviteUserPayload) =>
    createAction(InviteUserActionTypes.INVITE_USER_REQUEST, payload),
  inviteUserSuccess: () =>
    createAction(InviteUserActionTypes.INVITE_USER_SUCCESS),
  inviteUserFailure: (error: string) =>
    createAction(InviteUserActionTypes.INVITE_USER_FAILURE, error),
};
export type InviteUserAction = ActionsUnion<typeof InviteUserAction>;

export const DeleteInviteAction = {
  deleteInviteRequest: (payload: DeleteInvitePayload) =>
    createAction(DeleteInviteActionTypes.DELETE_INVITE_REQUEST, payload),
  deleteInviteSuccess: () =>
    createAction(DeleteInviteActionTypes.DELETE_INVITE_SUCCESS),
  deleteInviteFailure: (error: string) =>
    createAction(DeleteInviteActionTypes.DELETE_INVITE_FAILURE, error),
};
export type DeleteInviteAction = ActionsUnion<typeof DeleteInviteAction>;

export const AdminResetPasswordAction = {
  adminResetPasswordRequest: (payload: AdminResetPasswordPayload) =>
    createAction(
      AdminResetPasswordActionTypes.ADMIN_RESET_PASSWORD_REQUEST,
      payload
    ),
  adminResetPasswordSuccess: () =>
    createAction(AdminResetPasswordActionTypes.ADMIN_RESET_PASSWORD_SUCCESS),
  adminResetPasswordFailure: (error: string) =>
    createAction(
      AdminResetPasswordActionTypes.ADMIN_RESET_PASSWORD_FAILURE,
      error
    ),
};
export type AdminResetPasswordAction = ActionsUnion<
  typeof AdminResetPasswordAction
>;

export const ValidateTfaAction = {
  validateTFARequest: (payload: ValidateTfaPayload) =>
    createAction(ValidateTfaActionTypes.VALIDATE_TFA_REQUEST, payload),
  validateTFASuccess: () =>
    createAction(ValidateTfaActionTypes.VALIDATE_TFA_SUCCESS),
  validateTFAFailure: (error: string) =>
    createAction(ValidateTfaActionTypes.VALIDATE_TFA_FAILURE, error),
};
export type ValidateTfaAction = ActionsUnion<typeof ValidateTfaAction>;
