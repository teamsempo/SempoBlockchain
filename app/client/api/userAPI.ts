import { apiClient } from "./client/apiClient";
import {
  CreateUserPayload,
  DeleteUserPayload,
  EditUserPayload,
  LoadUserRequestPayload,
  ResetPinPayload,
  LoadUserHistoryPayload
} from "../reducers/user/types";

export const loadUserAPI = ({ query, path }: LoadUserRequestPayload) =>
  apiClient({ url: "/user/", method: "GET", query: query, path: path });

export const createUserAPI = ({ body }: CreateUserPayload) =>
  apiClient({ url: "/user/", method: "POST", body: body });

export const editUserAPI = ({ body, path }: EditUserPayload) =>
  apiClient({ url: "/user/", method: "PUT", body: body, path: path });

export const deleteUserAPI = ({ path }: DeleteUserPayload) =>
  apiClient({ url: "/user/", method: "DELETE", path: path });

export const resetPinAPI = ({ body }: ResetPinPayload) =>
  apiClient({ url: "/user/reset_pin/", method: "POST", body: body });

export const loadUserHistoryAPI = ({ query, path }: LoadUserHistoryPayload) =>
  apiClient({
    url: "/user/history/",
    method: "GET",
    query: query,
    path: path
  });
