import { apiClient } from "./client/apiClient";
import { LoadAsyncPayload } from "../reducers/async/types";

export const loadAsyncAPI = ({ path, query }: LoadAsyncPayload) =>
  apiClient({
    url: "/async/",
    method: "GET",
    query: query,
    path: path,
  });
