import { apiClient } from "./apiClient";

export const requestApiToken = ({ body }) =>
  apiClient({
    url: "/auth/request_api_token/",
    method: "POST",
    isAuthed: false,
    isTFA: true,
    body: body,
    errorHandling: false
  });

export const refreshApiToken = () =>
  apiClient({ url: "/auth/refresh_api_token/", method: "GET" });

export const registerAPI = ({ body }) =>
  apiClient({
    url: "/auth/register/",
    method: "POST",
    isAuthed: false,
    body: body,
    errorHandling: false
  });

export const activateAPI = ({ body }) =>
  apiClient({
    url: "/auth/activate/",
    method: "POST",
    isAuthed: false,
    body: body,
    errorHandling: false
  });

export const requestResetEmailAPI = ({ body }) =>
  apiClient({
    url: "/auth/request_reset_email/",
    method: "POST",
    isAuthed: false,
    body: body
  });

export const GetTFAAPI = () => apiClient({ url: "/auth/tfa/", method: "GET" });

export const ValidateTFAAPI = ({ body }) =>
  apiClient({ url: "/auth/tfa/", method: "POST", body: body });

export const ResetPasswordAPI = ({ body }) =>
  apiClient({ url: "/auth/reset_password/", method: "POST", body: body });

export const getUserList = () =>
  apiClient({ url: "/auth/permissions/", method: "GET" });

export const updateUserAPI = ({ body, query }) =>
  apiClient({
    url: "/auth/permissions/",
    method: "PUT",
    body: body,
    query: query
  });

export const deleteInviteAPI = ({ body }) =>
  apiClient({ url: "/auth/permissions/", method: "DELETE", body: body });

export const inviteUserAPI = ({ body }) =>
  apiClient({ url: "/auth/permissions/", method: "POST", body: body });
