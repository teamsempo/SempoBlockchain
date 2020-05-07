import {
  EditOrganisationActionTypes,
  EditOrganisationPayload,
  LoadOrganisationActionTypes,
  Organisation,
  OrganisationActionTypes
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const OrganisationAction = {
  updateOrganisationList: (organisations: Organisation[]) =>
    createAction(
      OrganisationActionTypes.UPDATE_ORGANISATION_LIST,
      organisations
    )
};
export type OrganisationAction = ActionsUnion<typeof OrganisationAction>;

export const LoadOrganisationAction = {
  loadOrganisationRequest: () =>
    createAction(LoadOrganisationActionTypes.LOAD_ORGANISATION_REQUEST),
  loadOrganisationSuccess: () =>
    createAction(LoadOrganisationActionTypes.LOAD_ORGANISATION_SUCCESS),
  loadOrganisationFailure: (error: string) =>
    createAction(LoadOrganisationActionTypes.LOAD_ORGANISATION_FAILURE, error)
};
export type LoadOrganisationAction = ActionsUnion<
  typeof LoadOrganisationAction
>;

export const EditOrganisationAction = {
  editOrganisationRequest: (payload: EditOrganisationPayload) =>
    createAction(
      EditOrganisationActionTypes.EDIT_ORGANISATION_REQUEST,
      payload
    ),
  editOrganisationSuccess: () =>
    createAction(EditOrganisationActionTypes.EDIT_ORGANISATION_SUCCESS),
  editOrganisationFailure: (error: string) =>
    createAction(EditOrganisationActionTypes.EDIT_ORGANISATION_FAILURE, error)
};
export type EditOrganisationAction = ActionsUnion<
  typeof EditOrganisationAction
>;
