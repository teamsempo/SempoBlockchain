import { apiClient } from "./client/apiClient";
import { API } from "./client/types";

export const loadUserAPI = ({ query, path }: API) =>
  apiClient({ url: "/user/", method: "GET", query: query, path: path });

export const createUserAPI = ({ body }: API) =>
  apiClient({ url: "/user/", method: "POST", body: body });

export const editUserAPI = ({ body, path }: API) =>
  apiClient({ url: "/user/", method: "PUT", body: body, path: path });

export const deleteUserAPI = ({ path }: API) =>
  apiClient({ url: "/user/", method: "DELETE", path: path });

export const resetPinAPI = ({ body }: API) =>
  apiClient({ url: "/user/reset_pin/", method: "POST", body: body });
