import { LOAD_ORGANISATION_REQUEST, LoadOrganisationsAction } from "./types";

export const loadOrganisation = (): LoadOrganisationsAction => ({
  type: LOAD_ORGANISATION_REQUEST
});
