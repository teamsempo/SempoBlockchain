import { apiClient } from "./client/apiClient";
import {
  EditTransferAccountPayload,
  LoadTransferAccountListPayload
} from "../reducers/transferAccount/types";

export const loadTransferAccountListAPI = ({
  query,
  path
}: LoadTransferAccountListPayload) =>
  apiClient({
    url: "/search/",
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
