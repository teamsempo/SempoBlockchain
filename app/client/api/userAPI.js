import { apiClient } from "./apiClient";

export const loadUserAPI = ({ query, path }) =>
  apiClient({ url: "/user/", method: "GET", query: query, path: path });

export const createUserAPI = ({ body }) =>
  apiClient({ url: "/user/", method: "POST", body: body });

export const editUserAPI = ({ body, path }) =>
  apiClient({ url: "/user/", method: "PUT", body: body, path: path });

export const deleteUserAPI = ({ path }) =>
  apiClient({ url: "/user/", method: "DELETE", path: path });

export const resetPinAPI = ({ body }) =>
  apiClient({ url: "/user/reset_pin/", method: "POST", body: body });
