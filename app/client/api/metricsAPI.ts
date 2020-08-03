import { LoadMetricsPayload } from "../reducers/metric/types";
import { apiClient } from "./client/apiClient";

export const loadCreditTransferStatsAPI = ({
  query,
  path
}: LoadMetricsPayload) =>
  apiClient({
    url: "/metrics/",
    method: "GET",
    query: query,
    path: path
  });
