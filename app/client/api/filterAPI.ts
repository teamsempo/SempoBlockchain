import { apiClient } from "./client/apiClient";
import { CreateFilterPayload } from "../reducers/filter/types";
import { LoadAllowedFiltersPayload } from "../reducers/metric/types";

export const loadSavedFilters = () =>
  apiClient({ url: "/filters/", method: "GET" });

export const createFilterAPI = ({ body }: CreateFilterPayload) =>
  apiClient({ url: "/filters/", method: "POST", body: body });

export const loadAllowedFiltersAPI = ({
  query,
  filterObject
}: LoadAllowedFiltersPayload) =>
  apiClient({
    // url: `/${filterObject ? filterObject : "metrics"}/filters/`,
    url: `/metrics/filters/`,
    method: "GET",
    query: query
  });
