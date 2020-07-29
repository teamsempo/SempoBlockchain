import { apiClient } from "./client/apiClient";
import { LoadTransferUsagePayload } from "../reducers/transferUsage/types";

export const loadTransferUsagesAPI = ({ query }: LoadTransferUsagePayload) =>
  apiClient({ url: "/transfer_usage/", method: "GET", query: query });
