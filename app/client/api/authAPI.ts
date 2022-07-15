import { apiClient } from "./client/apiClient";
import {
  ActivatePayload,
  DeleteInvitePayload,
  InviteUserPayload,
  LoginRequestPayload,
  RegisterRequestPayload,
  ResetEmailPayload,
  ResetPasswordPayload,
  UpdateUserPayload,
  ValidateTfaPayload,
  AdminResetPasswordPayload,
} from "../reducers/auth/types";

export const requestApiToken = ({ body }: LoginRequestPayload) =>
  apiClient({
    url: "/auth/request_api_token/",
    method: "POST",
    isAuthed: false,
    isTFA: true,
    body: body,
    errorHandling: false,
  });

export const refreshApiToken = () =>
  apiClient({ url: "/auth/refresh_api_token/", method: "GET" });

export const registerAPI = ({ body }: RegisterRequestPayload) =>
  apiClient({
    url: "/auth/register/",
    method: "POST",
    isAuthed: false,
    body: body,
    errorHandling: false,
  });

export const activateAPI = ({ body }: ActivatePayload) =>
  apiClient({
    url: "/auth/activate/",
    method: "POST",
    isAuthed: false,
    body: body,
    errorHandling: false,
  });

export const requestResetEmailAPI = ({ body }: ResetEmailPayload) =>
  apiClient({
    url: "/auth/request_reset_email/",
    method: "POST",
    isAuthed: false,
    body: body,
  });

export const GetTFAAPI = () => apiClient({ url: "/auth/tfa/", method: "GET" });

export const ValidateTFAAPI = ({ body }: ValidateTfaPayload) =>
  apiClient({ url: "/auth/tfa/", method: "POST", body: body });

export const ResetPasswordAPI = ({ body }: ResetPasswordPayload) =>
  apiClient({ url: "/auth/reset_password/", method: "POST", body: body });

export const logoutAPI = () =>
  apiClient({ url: "/auth/logout/", method: "POST" });

export const getUserList = () =>
  apiClient({ url: "/auth/permissions/", method: "GET" });

export const updateUserAPI = ({ body, query }: UpdateUserPayload) =>
  apiClient({
    url: "/auth/permissions/",
    method: "PUT",
    body: body,
    query: query,
  });

export const deleteInviteAPI = ({ body }: DeleteInvitePayload) =>
  apiClient({ url: "/auth/permissions/", method: "DELETE", body: body });

export const inviteUserAPI = ({ body }: InviteUserPayload) =>
  apiClient({ url: "/auth/permissions/", method: "POST", body: body });

export const adminResetPasswordAPI = ({ path }: AdminResetPasswordPayload) =>
  apiClient({
    url: "/user/password-reset/",
    method: "PUT",
    path: path,
  });
