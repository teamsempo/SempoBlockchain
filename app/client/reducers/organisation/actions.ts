import {
  CreateOrganisationActionTypes,
  CreateOrganisationPayload,
  EditOrganisationActionTypes,
  EditOrganisationPayload,
  LoadOrganisationActionTypes,
  OrganisationActionTypes,
  OrganisationByIDs
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const OrganisationAction = {
  updateOrganisationList: (organisations: OrganisationByIDs) =>
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

export const CreateOrganisationAction = {
  createOrganisationRequest: (payload: CreateOrganisationPayload) =>
    createAction(
      CreateOrganisationActionTypes.CREATE_ORGANISATION_REQUEST,
      payload
    ),
  createOrganisationSuccess: () =>
    createAction(CreateOrganisationActionTypes.CREATE_ORGANISATION_SUCCESS),
  createOrganisationFailure: (error: string) =>
    createAction(
      CreateOrganisationActionTypes.CREATE_ORGANISATION_FAILURE,
      error
    )
};
export type CreateOrganisationAction = ActionsUnion<
  typeof CreateOrganisationAction
>;
