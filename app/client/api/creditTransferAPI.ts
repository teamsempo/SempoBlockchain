import { apiClient } from "./client/apiClient";

import {
  CreateCreditTransferPayload,
  LoadCreditTransferPayload,
  ModifyCreditTransferRequestPayload,
  LoadTransferAccountListPayload
} from "../reducers/creditTransfer/types";

export const newLoadTransferAccountListAPI = ({
  query,
  path
}: LoadTransferAccountListPayload) =>
  apiClient({
    url: "/credit_transfer/",
    method: "GET",
    query: query,
    path: path
  });

export const loadCreditTransferListAPI = ({
  query,
  path
}: LoadCreditTransferPayload) =>
  apiClient({
    url: "/credit_transfer/",
    method: "GET",
    query: query,
    path: path
  });

export const modifyTransferAPI = ({
  body,
  path
}: ModifyCreditTransferRequestPayload) =>
  apiClient({
    url: "/credit_transfer/",
    method: "PUT",
    body: body,
    path: path
  });

export const newTransferAPI = ({ body }: CreateCreditTransferPayload) =>
  apiClient({ url: "/credit_transfer/", method: "POST", body: body });
