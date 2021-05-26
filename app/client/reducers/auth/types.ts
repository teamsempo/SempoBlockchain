import { Organisation } from "../organisation/types";

export enum LoginActionTypes {
  REAUTH_REQUEST = "REAUTH_REQUEST",
  LOGIN_REQUEST = "LOGIN_REQUEST",
  UPDATE_ACTIVE_ORG = "UPDATE_ACTIVE_ORG",
  LOGOUT = "LOGOUT",
  API_LOGOUT = "API_LOGOUT",
  LOGIN_PARTIAL = "LOGIN_PARTIAL",
  LOGIN_SUCCESS = "LOGIN_SUCCESS",
  LOGIN_FAILURE = "LOGIN_FAILURE"
}

export interface UpdateActiveOrgPayload {
  organisationIds: number[];
  isManageWallet?: boolean;
}

export interface LoginRequestPayload {
  body: {
    username: string;
    password: string;
  };
}

export interface LoginPartialPayload {
  error: null | string;
  tfaURL: null | string;
  tfaFailure: boolean;
}

export interface LoginSuccessPayload {
  token: null | string;
  userId: null | number;
  email: null | string;
  intercomHash: null | string;
  webApiVersion: null | string;
  organisationId: number;
  organisationIds: null | string[];
  usdToSatoshiRate: null | number;
  adminTier?: string;
}

export enum RegisterActionTypes {
  REGISTER_REQUEST = "REGISTER_REQUEST",
  REGISTER_SUCCESS = "REGISTER_SUCCESS",
  REGISTER_FAILURE = "REGISTER_FAILURE",
  REGISTER_INACTIVE = "REGISTER_INACTIVE"
}

// export const REGISTER_REQUEST = "REGISTER_REQUEST";
export interface RegisterRequestPayload {
  body: {
    username: string;
    password: string;
    referral_code: string;
  };
}

export enum ActivateActionTypes {
  ACTIVATE_REQUEST = "ACTIVATE_REQUEST",
  ACTIVATE_SUCCESS = "ACTIVATE_SUCCESS",
  ACTIVATE_FAILURE = "ACTIVATE_FAILURE"
}

export interface ActivatePayload {
  body: {
    activation_token: string;
  };
}

export enum ResetPasswordEmailActionTypes {
  REQUEST_RESET_REQUEST = "REQUEST_RESET_REQUEST",
  REQUEST_RESET_SUCCESS = "REQUEST_RESET_SUCCESS",
  REQUEST_RESET_FAILURE = "REQUEST_RESET_FAILURE"
}

export interface ResetEmailPayload {
  body: {
    email: string;
  };
}

export enum ResetPasswordActionTypes {
  RESET_PASSWORD_REQUEST = "RESET_PASSWORD_REQUEST",
  RESET_PASSWORD_SUCCESS = "RESET_PASSWORD_SUCCESS",
  RESET_PASSWORD_FAILURE = "RESET_PASSWORD_FAILURE"
}

export interface ResetPasswordPayload {
  body: {
    new_password: string;
    reset_password_token: string;
    old_password: string;
  };
}

export interface AdminUser {
  id: number;
  email: string;
  admin_tier: string;
  created: string;
  is_activated: boolean;
  is_disabled: boolean;
}

export interface AdminUserByIDs {
  [key: number]: AdminUser;
}

export const UPDATE_ADMIN_USER_LIST = "UPDATE_ADMIN_USER_LIST";

export interface Invite {
  id: number;
  email: string;
  admin_tier: string;
  created: string;
}

export interface InviteByIDs {
  [key: number]: Invite;
}

export enum InviteUserListActionTypes {
  DEEP_UPDATE_INVITE_USER_LIST = "DEEP_UPDATE_INVITE_USER_LIST",
  UPDATE_INVITE_USER_LIST = "UPDATE_INVITE_USER_LIST"
}

export enum LoadAdminUserListActionTypes {
  LOAD_ADMIN_USER_REQUEST = "LOAD_ADMIN_USER_REQUEST",
  LOAD_ADMIN_USER_SUCCESS = "LOAD_ADMIN_USER_SUCCESS",
  LOAD_ADMIN_USER_FAILURE = "LOAD_ADMIN_USER_FAILURE"
}

export enum EditAdminUserActionTypes {
  EDIT_ADMIN_USER_REQUEST = "EDIT_ADMIN_USER_REQUEST",
  EDIT_ADMIN_USER_SUCCESS = "EDIT_ADMIN_USER_SUCCESS",
  EDIT_ADMIN_USER_FAILURE = "EDIT_ADMIN_USER_FAILURE"
}

export interface UpdateUserPayload {
  body: {
    user_id: number;
    admin_tier: string;
    deactivated: boolean;
  };
  query: {};
}

export enum InviteUserActionTypes {
  INVITE_USER_REQUEST = "INVITE_USER_REQUEST",
  INVITE_USER_SUCCESS = "INVITE_USER_SUCCESS",
  INVITE_USER_FAILURE = "INVITE_USER_FAILURE"
}

export interface InviteUserPayload {
  body: {
    email: string;
    tier: string;
  };
}

export enum DeleteInviteActionTypes {
  DELETE_INVITE_REQUEST = "DELETE_INVITE_REQUEST",
  DELETE_INVITE_SUCCESS = "DELETE_INVITE_SUCCESS",
  DELETE_INVITE_FAILURE = "DELETE_INVITE_FAILURE"
}

export interface DeleteInvitePayload {
  body: {
    invite_id: number;
  };
}

export enum ValidateTfaActionTypes {
  VALIDATE_TFA_REQUEST = "VALIDATE_TFA_REQUEST",
  VALIDATE_TFA_SUCCESS = "VALIDATE_TFA_SUCCESS",
  VALIDATE_TFA_FAILURE = "VALIDATE_TFA_FAILURE"
}

export interface ValidateTfaPayload {
  body: {
    otp: string;
    otp_expiry_interval: number;
  };
}

export interface TokenData {
  auth_token: string;
  user_id: number;
  email: string;
  admin_tier: string;
  usd_to_satoshi_rate: null | number;
  web_intercom_hash: string;
  web_api_version: string;
  active_organisation_id: number;
  organisation_ids: string[];
}

export interface OrganisationLoginData extends TokenData {
  organisations: Organisation[];
  organisation: Organisation;
}

export interface AdminData {
  admin: AdminUser[];
  admins: AdminUser[];
  invites: Invite[];
  invite: Invite;
}
