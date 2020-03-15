export const LoginActionTypes = {
  REAUTH_REQUEST: "REAUTH_REQUEST",
  LOGIN_REQUEST: "LOGIN_REQUEST",
  UPDATE_ACTIVE_ORG: "UPDATE_ACTIVE_ORG",
  LOGOUT: "LOGOUT",
  LOGIN_PARTIAL: "LOGIN_PARTIAL",
  LOGIN_SUCCESS: "LOGIN_SUCCESS",
  LOGIN_FAILURE: "LOGIN_FAILURE"
};

export interface UpdateActiveOrgPayload {
  organisationName: string;
  organisationId: number;
  organisationToken: string;
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
  vendorId: null | number;
  intercomHash: null | string;
  webApiVersion: null | string;
  organisationName: null | string;
  organisationId: null | number;
  organisationToken: null | string;
  usdToSatoshiRate: null | number;
  organisations?: string[];
  requireTransferCardExists: null | boolean;
  adminTier?: string;
}

export const RegisterActionTypes = {
  REGISTER_REQUEST: "REGISTER_REQUEST",
  REGISTER_SUCCESS: "REGISTER_SUCCESS",
  REGISTER_FAILURE: "REGISTER_FAILURE",
  REGISTER_INACTIVE: "REGISTER_INACTIVE"
};

// export const REGISTER_REQUEST = "REGISTER_REQUEST";
export interface RegisterRequestPayload {
  body: {
    username: string;
    password: string;
    referral_code: string;
  };
}

export const ActivateActionTypes = {
  ACTIVATE_REQUEST: "ACTIVATE_REQUEST",
  ACTIVATE_SUCCESS: "ACTIVATE_SUCCESS",
  ACTIVATE_FAILURE: "ACTIVATE_FAILURE"
};

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

export const ResetPasswordActionTypes = {
  RESET_PASSWORD_REQUEST: "RESET_PASSWORD_REQUEST",
  RESET_PASSWORD_SUCCESS: "RESET_PASSWORD_SUCCESS",
  RESET_PASSWORD_FAILURE: "RESET_PASSWORD_FAILURE"
};

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
export const UPDATE_ADMIN_USER_LIST = "UPDATE_ADMIN_USER_LIST";

export interface Invite {
  id: number;
  email: string;
  admin_tier: string;
  created: string;
}

export const InviteUserListActionTypes = {
  DEEP_UPDATE_INVITE_USER_LIST: "DEEP_UPDATE_INVITE_USER_LIST",
  UPDATE_INVITE_USER_LIST: "UPDATE_INVITE_USER_LIST"
};

export const LoadAdminUserListActionTypes = {
  LOAD_ADMIN_USER_REQUEST: "LOAD_ADMIN_USER_REQUEST",
  LOAD_ADMIN_USER_SUCCESS: "LOAD_ADMIN_USER_SUCCESS",
  LOAD_ADMIN_USER_FAILURE: "LOAD_ADMIN_USER_FAILURE"
};

export const EditAdminUserActionTypes = {
  EDIT_ADMIN_USER_REQUEST: "EDIT_ADMIN_USER_REQUEST",
  EDIT_ADMIN_USER_SUCCESS: "EDIT_ADMIN_USER_SUCCESS",
  EDIT_ADMIN_USER_FAILURE: "EDIT_ADMIN_USER_FAILURE"
};

export interface UpdateUserPayload {
  body: {
    user_id: number;
    admin_tier: string;
    deactivated: boolean;
  };
  query: {};
}

export const InviteUserActionTypes = {
  INVITE_USER_REQUEST: "INVITE_USER_REQUEST",
  INVITE_USER_SUCCESS: "INVITE_USER_SUCCESS",
  INVITE_USER_FAILURE: "INVITE_USER_FAILURE"
};

export interface InviteUserPayload {
  body: {
    email: string;
    tier: string;
  };
}

export const DeleteInviteActionTypes = {
  DELETE_INVITE_REQUEST: "DELETE_INVITE_REQUEST",
  DELETE_INVITE_SUCCESS: "DELETE_INVITE_SUCCESS",
  DELETE_INVITE_FAILURE: "DELETE_INVITE_FAILURE"
};

export interface DeleteInvitePayload {
  body: {
    invite_id: number;
  };
}

export const ValidateTfaActionTypes = {
  VALIDATE_TFA_REQUEST: "VALIDATE_TFA_REQUEST",
  VALIDATE_TFA_SUCCESS: "VALIDATE_TFA_SUCCESS",
  VALIDATE_TFA_FAILURE: "VALIDATE_TFA_FAILURE"
};

export interface ValidateTfaPayload {
  body: {
    otp: string;
    otp_expiry_interval: number;
  };
}
