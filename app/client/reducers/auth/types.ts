export const REAUTH_REQUEST = 'REAUTH_REQUEST';
export interface ReauthRequest {type: typeof REAUTH_REQUEST}
export const UPDATE_ACTIVE_ORG = 'UPDATE_ACTIVE_ORG';
export interface UpdateActiveOrgPayload {
  organisationName: string,
  organisationId: number
}
interface UpdateActiveOrg {
  type: typeof UPDATE_ACTIVE_ORG,
  payload: UpdateActiveOrgPayload
}
export const LOGIN_REQUEST = 'LOGIN_REQUEST';
export interface LoginRequestPayload {
  body: {
    username: string,
    password: string
  }
}
interface LoginRequest {
  type: typeof LOGIN_REQUEST,
  payload: LoginRequestPayload
}
export const LOGIN_PARTIAL = 'LOGIN_PARTIAL';
export interface LoginPartial {
  type: typeof LOGIN_PARTIAL,
  error: null,
  tfaURL: null,
  tfaFailure: false
}
export const LOGIN_SUCCESS = 'LOGIN_SUCCESS';
export interface LoginSuccess {
  type: typeof LOGIN_SUCCESS,
  token: null | string,
  userId: null | number,
  email: null | string,
  vendorId: null | number,
  intercomHash: null | string,
  webApiVersion: null | string,
  organisationName: null | string,
  organisationId: null | number,
  usdToSatoshiRate: null | number,
  organisations?: string[],
  requireTransferCardExists: null | boolean,
  adminTier?: string
}
export const LOGIN_FAILURE = 'LOGIN_FAILURE';
export interface LoginFailure {
  type: typeof LOGIN_FAILURE,
  error: string
}
export const LOGOUT = 'LOGOUT';
export interface LogoutRequest {type: typeof LOGOUT}
export type LoginAction = ReauthRequest | LoginRequest | UpdateActiveOrg | LogoutRequest | LoginPartial | LoginSuccess | LoginFailure

export const REGISTER_REQUEST = 'REGISTER_REQUEST';
export interface RegisterRequestPayload {
  body: {
    username: string,
    password: string,
    referral_code: string
  }
}
interface RegisterRequest {
  type: typeof REGISTER_REQUEST,
  payload: RegisterRequestPayload
}
export const REGISTER_SUCCESS = 'REGISTER_SUCCESS';
export interface RegisterSuccess {type: typeof REGISTER_SUCCESS}
export const REGISTER_FAILURE = 'REGISTER_FAILURE';
export interface RegisterFailure {
  type: typeof REGISTER_FAILURE,
  error: string
}
export const REGISTER_INACTIVE = 'REGISTER_INACTIVE';
export interface RegisterInactive {type: typeof REGISTER_INACTIVE}
export type RegisterAction = RegisterRequest | RegisterSuccess | RegisterFailure | RegisterInactive

export const ACTIVATE_REQUEST = 'ACTIVATE_REQUEST';
export interface ActivateRequest {
  type: typeof ACTIVATE_REQUEST,
  activation_token: string
}
export const ACTIVATE_SUCCESS = 'ACTIVATE_SUCCESS';
interface ActivateSuccess {type: typeof ACTIVATE_SUCCESS}
export const ACTIVATE_FAILURE = 'ACTIVATE_FAILURE';
interface ActivateFailure {
  type: typeof ACTIVATE_FAILURE,
  error: string
}
export type ActivateAction = ActivateRequest | ActivateSuccess | ActivateFailure

export const REQUEST_RESET_REQUEST = 'REQUEST_RESET_REQUEST';
export interface ResetEmailRequest {
  type: typeof REQUEST_RESET_REQUEST,
  email: string
}
export const REQUEST_RESET_SUCCESS = 'REQUEST_RESET_SUCCESS';
interface ResetEmailSuccess {type: typeof REQUEST_RESET_SUCCESS}
export const REQUEST_RESET_FAILURE = 'REQUEST_RESET_FAILURE';
interface ResetEmailFailure {
  type: typeof REQUEST_RESET_FAILURE,
  error: string
}
export type ResetEmailAction = ResetEmailRequest | ResetEmailSuccess | ResetEmailFailure

export const RESET_PASSWORD_REQUEST = 'RESET_PASSWORD_REQUEST';
export interface ResetPasswordPayload {
  new_password: string,
  reset_password_token: string,
  old_password: string
}
interface ResetPasswordRequest {
  type: typeof RESET_PASSWORD_REQUEST,
  payload: ResetPasswordPayload
}
export const RESET_PASSWORD_SUCCESS = 'RESET_PASSWORD_SUCCESS';
interface ResetPasswordSuccess {type: typeof RESET_PASSWORD_SUCCESS}
export const RESET_PASSWORD_FAILURE = 'RESET_PASSWORD_FAILURE';
interface ResetPasswordFailure {
  type: typeof RESET_PASSWORD_FAILURE,
  error: string
}
export type ResetPasswordAction = ResetPasswordRequest | ResetPasswordSuccess | ResetPasswordFailure

export const USER_LIST_REQUEST = 'USER_LIST_REQUEST';
interface UserListRequest { type: typeof USER_LIST_REQUEST }
export const USER_LIST_SUCCESS = 'USER_LIST_SUCCESS';
interface UserListSuccess {
  type: typeof USER_LIST_SUCCESS,
  load_result: {
    //TODO(refactor): what is userList data actually?
    admin_list: string[]
  }
}
export const USER_LIST_FAILURE = 'USER_LIST_FAILURE';
interface UserListFailure {
  type: typeof USER_LIST_FAILURE,
  error: string
}
export type UserListAction = UserListRequest | UserListSuccess | UserListFailure

export const UPDATE_USER_REQUEST = 'UPDATE_USER_REQUEST';
export interface UpdateUserPayload {
  body: {
    user_id: number,
    admin_tier: string,
    deactivated: boolean,
  },
  query: {
  }
}
interface UpdateUserRequest {
  type: typeof UPDATE_USER_REQUEST,
  payload: UpdateUserPayload
}
export const UPDATE_USER_SUCCESS = 'UPDATE_USER_SUCCESS';
interface UpdateUserSuccess {type: typeof UPDATE_USER_SUCCESS}
export const UPDATE_USER_FAILURE = 'UPDATE_USER_FAILURE';
interface UpdateUserFailure {
  type: typeof UPDATE_USER_FAILURE,
  error: string
}
export type UpdateUserAction = UpdateUserRequest | UpdateUserSuccess | UpdateUserFailure

export const INVITE_USER_REQUEST = 'INVITE_USER_REQUEST';
export interface InviteUserPayload {
  body: {
    email: string,
    tier: string
  }
}
interface InviteUserRequest {
  type: typeof INVITE_USER_REQUEST,
  payload: InviteUserPayload
}
export const INVITE_USER_SUCCESS = 'INVITE_USER_SUCCESS';
interface InviteUserSuccess {type: typeof INVITE_USER_SUCCESS}
export const INVITE_USER_FAILURE = 'INVITE_USER_FAILURE';
interface InviteUserFailure {
  type: typeof INVITE_USER_FAILURE,
  error: string
}
export type InviteUserAction = InviteUserRequest | InviteUserSuccess | InviteUserFailure

export const VALIDATE_TFA_REQUEST = 'VALIDATE_TFA_REQUEST';
export interface ValidateTfaPayload {
  otp: string,
  otp_expiry_interval: number
}
interface ValidateTfaRequest {
  type: typeof VALIDATE_TFA_REQUEST,
  payload: ValidateTfaPayload
}
export const VALIDATE_TFA_SUCCESS = 'VALIDATE_TFA_SUCCESS';
interface ValidateTfaSuccess {type: typeof VALIDATE_TFA_SUCCESS}
export const VALIDATE_TFA_FAILURE = 'VALIDATE_TFA_FAILURE';
interface ValidateTfaFailure {
  type: typeof VALIDATE_TFA_FAILURE,
  error: string
}
export type ValidateTfaAction = ValidateTfaRequest | ValidateTfaSuccess | ValidateTfaFailure
