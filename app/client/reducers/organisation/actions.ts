import {
  LOAD_ORGANISATION_REQUEST,
  LoadOrganisationsAction,
  EDIT_ORGANISATION_REQUEST,
  EditOrganisationAction,
  EditOrganisationPayload
} from "./types";

export const loadOrganisation = (): LoadOrganisationsAction => ({
  type: LOAD_ORGANISATION_REQUEST
});

export const editOrganisation = (
  payload: EditOrganisationPayload
): EditOrganisationAction => ({
  type: EDIT_ORGANISATION_REQUEST,
  payload
});
