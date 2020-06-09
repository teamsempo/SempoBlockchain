import { apiClient } from "./client/apiClient";

export const loadTransferAccountListAPI = ({ query, path }) =>
  apiClient({
    url: "/transfer_account/",
    method: "GET",
    query: query,
    path: path
  });

export const editTransferAccountAPI = ({ body, path }) =>
  apiClient({
    url: "/transfer_account/",
    method: "PUT",
    body: body,
    path: path
  });
