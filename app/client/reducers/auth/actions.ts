import {
  ACTIVATE_REQUEST,
  INVITE_USER_REQUEST, InviteUserPayload,
  LOGIN_FAILURE,
  LOGIN_REQUEST, LoginRequestPayload,
  LOGOUT,
  REGISTER_FAILURE,
  REGISTER_INACTIVE,
  REGISTER_REQUEST,
  REGISTER_SUCCESS,
  RegisterRequestPayload,
  REQUEST_RESET_REQUEST,
  RESET_PASSWORD_REQUEST, ResetPasswordPayload,
  UPDATE_ACTIVE_ORG,
  EDIT_ADMIN_USER_REQUEST, UpdateActiveOrgPayload, UpdateUserPayload,
  LOAD_ADMIN_USER_REQUEST,
  VALIDATE_TFA_REQUEST, ValidateTfaPayload, DELETE_INVITE_REQUEST, DeleteInvitePayload
} from "./types";

export const updateActiveOrgRequest = (payload: UpdateActiveOrgPayload) => (
  {
    type: UPDATE_ACTIVE_ORG,
    payload
  }
);

export const loginRequest = (payload: LoginRequestPayload) => (
  {
    type: LOGIN_REQUEST,
    payload,
  }
);

export const loginFailure = (error: string) => (
  {
    type: LOGIN_FAILURE,
    error
  }
);

export const logout = () => (
  {
    type: LOGOUT
  }
);

export const registerRequest = (payload: RegisterRequestPayload) => (
  {
    type: REGISTER_REQUEST,
    payload
  }
);

export const registerSuccess = () => (
  {
    type: REGISTER_SUCCESS
  }
);

export const registerFailure = (error: string) => (
  {
    type: REGISTER_FAILURE,
    error
  }
);

export const deactivateRegister = () => (
  {
    type: REGISTER_INACTIVE
  }
);

export const activateAccount = (activation_token: string) => (
  {
    type: ACTIVATE_REQUEST,
    activation_token
  }
);

export const requestPasswordResetEmail = (email: string) => (
  {
    type: REQUEST_RESET_REQUEST,
    email
  }
);

export const resetPassword = (payload: ResetPasswordPayload) => (
  {
    type: RESET_PASSWORD_REQUEST,
    payload
  }
);

export const loadUserList = () => (
  {
    type: LOAD_ADMIN_USER_REQUEST,
  }
);

export const updateUser = (payload: UpdateUserPayload) => (
  {
    type: EDIT_ADMIN_USER_REQUEST,
    payload
  }
);

export const inviteUser = (payload: InviteUserPayload) => (
  {
    type: INVITE_USER_REQUEST,
    payload
  }
);


export const deleteInvite = (payload: DeleteInvitePayload) => (
  {
    type: DELETE_INVITE_REQUEST,
    payload
  }
);

export const validateTFARequest = (payload: ValidateTfaPayload) => (
  {
    type: VALIDATE_TFA_REQUEST,
    payload
  }
);
