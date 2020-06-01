import { apiClient } from "./client/apiClient";
import { CreateFilterPayload } from "../reducers/filter/types";

export const loadFiltersAPI = () =>
  apiClient({ url: "/filters/", method: "GET" });

export const createFilterAPI = ({ body }: CreateFilterPayload) =>
  apiClient({ url: "/filters/", method: "POST", body: body });
