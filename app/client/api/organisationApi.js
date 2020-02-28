import { apiClient } from "./apiClient";

export const loadOrganisationAPI = () =>
  apiClient({ url: "/me/organisation/", method: "GET" });
