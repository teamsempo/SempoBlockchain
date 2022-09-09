import { apiClient } from "./client/apiClient";
import { LoadAsnycPayload } from "../reducers/async/types";

export const LoadAsyncAPI = ({ query, path }: LoadAsnycPayload) =>
  apiClient({
    url: "/credit_transfer/",
    method: "GET",
    query: query,
    path: path,
  });
