import { apiClient } from "./client/apiClient";
import {
  CreateOrganisationPayload,
  EditOrganisationPayload
} from "../reducers/organisation/types";

export const loadOrganisationAPI = () =>
  apiClient({ url: "/me/organisation/", method: "GET" });

export const editOrganisationAPI = ({ body, path }: EditOrganisationPayload) =>
  apiClient({ url: "/organisation/", method: "PUT", body: body, path: path });

export const createOrganisationAPI = ({ body }: CreateOrganisationPayload) =>
  apiClient({ url: "/organisation/", method: "POST", body: body });
