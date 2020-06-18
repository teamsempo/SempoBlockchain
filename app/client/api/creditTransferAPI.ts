import { apiClient } from "./client/apiClient";

import {
  LoadCreditTransferPayload,
  ModifyCreditTransferRequestPayload,
  CreateCreditTransferPayload
} from "../reducers/creditTransfer/types";
import { LoadMetricsPayload } from "../reducers/metric/types";

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

export const loadCreditTransferStatsAPI = ({
  query,
  path
}: LoadMetricsPayload) =>
  apiClient({
    url: "/credit_transfer/stats/",
    method: "GET",
    query: query,
    path: path
  });

export const loadCreditTransferFiltersAPI = () =>
  apiClient({
    url: "/credit_transfer/filters/",
    method: "GET"
  });
