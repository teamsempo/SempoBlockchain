import {LOAD_ORGANISATION_REQUEST, LoadOrganisationAction} from "./types";

export const loadOrganisation = (): LoadOrganisationAction => (
  {
    type: LOAD_ORGANISATION_REQUEST,
  }
);
