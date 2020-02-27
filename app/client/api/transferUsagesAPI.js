import { apiClient } from "./apiClient";

export const loadTransferUsagesAPI = ({ query }) =>
  apiClient({ url: "/transfer_usage/", method: "GET", query: query });
