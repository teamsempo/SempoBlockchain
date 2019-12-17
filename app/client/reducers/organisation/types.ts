export interface Organisation {
  name: string,
  token: {
    symbol: string
  }
}
export const UPDATE_ORGANISATION = "UPDATE_ORGANISATION";
interface UpdateOrganisation {
  type: typeof UPDATE_ORGANISATION,
  organisation: Organisation
}

export type OrganisationAction = UpdateOrganisation

export const LOAD_ORGANISATION_REQUEST = "LOAD_ORGANISATIONS_REQUEST";
interface LoadOrganisationRequest {
  type: typeof LOAD_ORGANISATION_REQUEST,
  id: string
}
export const LOAD_ORGANISATION_SUCCESS = "LOAD_ORGANISATIONS_SUCCESS";
interface LoadOrganisationSuccess {
  type: typeof LOAD_ORGANISATION_SUCCESS,
}
export const LOAD_ORGANISATION_FAILURE = "LOAD_ORGANISATIONS_FAILURE";
interface LoadOrganisationFailure {
  type: typeof LOAD_ORGANISATION_FAILURE,
  error: string
}

export type LoadOrganisationAction = LoadOrganisationRequest | LoadOrganisationSuccess | LoadOrganisationFailure
