import { apiClient } from "./client/apiClient";

import {
  CreateCreditTransferPayload,
  LoadCreditTransferPayload,
  ModifyCreditTransferRequestPayload
} from "../reducers/creditTransfer/types";

export const loadCreditTransferListAPI = ({
  query
}: LoadCreditTransferPayload) =>
  apiClient({
    url: "/credit_transfer/",
    method: "GET",
    query: query
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
