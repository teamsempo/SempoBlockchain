import { apiClient } from "./client/apiClient";
import { EditOrganisationPayload } from "../reducers/organisation/types";

export const loadOrganisationAPI = () =>
  apiClient({ url: "/me/organisation/", method: "GET" });

export const editOrganisationAPI = ({ body, path }: EditOrganisationPayload) =>
  apiClient({ url: "/organisation/", method: "PUT", body: body, path: path });
