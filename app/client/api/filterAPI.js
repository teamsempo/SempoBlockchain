import { apiClient } from "./client/apiClient";

export const loadFiltersAPI = () =>
  apiClient({ url: "/filters/", method: "GET" });

export const createFilterAPI = ({ body }) =>
  apiClient({ url: "/filters/", method: "POST", body: body });
