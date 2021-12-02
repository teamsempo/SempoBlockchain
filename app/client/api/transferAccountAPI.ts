import { apiClient } from "./client/apiClient";
import {
  EditTransferAccountPayload,
  LoadTransferAccountListPayload,
  LoadTransferAccountHistoryPayload
} from "../reducers/transferAccount/types";

export const loadTransferAccountListAPI = ({
  query,
  path
}: LoadTransferAccountListPayload) =>
  apiClient({
    url: "/transfer_account/",
    method: "GET",
    query: query,
    path: path
  });

export const editTransferAccountAPI = ({
  body,
  path
}: EditTransferAccountPayload) =>
  apiClient({
    url: "/transfer_account/",
    method: "PUT",
    body: body,
    path: path
  });

export const loadTransferAccountHistoryAPI = ({
  query,
  path
}: LoadTransferAccountHistoryPayload) =>
  apiClient({
    url: "/transfer_account/history/",
    method: "GET",
    query: query,
    path: path
  });
