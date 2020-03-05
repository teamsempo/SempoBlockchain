export interface Organisation {
  name: string;
  token: {
    symbol: string;
  };
  require_transfer_card: boolean;
  default_disbursement: number;
}

export const UPDATE_ORGANISATION_LIST = "UPDATE_ORGANISATION_LIST";

interface UpdateOrganisationList {
  type: typeof UPDATE_ORGANISATION_LIST;
  organisations: Organisation;
}

export type OrganisationAction = UpdateOrganisationList;

export const LOAD_ORGANISATION_REQUEST = "LOAD_ORGANISATIONS_REQUEST";

interface LoadOrganisationsRequest {
  type: typeof LOAD_ORGANISATION_REQUEST;
}
export const LOAD_ORGANISATION_SUCCESS = "LOAD_ORGANISATIONS_SUCCESS";

interface LoadOrganisationsSuccess {
  type: typeof LOAD_ORGANISATION_SUCCESS;
}
export const LOAD_ORGANISATION_FAILURE = "LOAD_ORGANISATIONS_FAILURE";

interface LoadOrganisationsFailure {
  type: typeof LOAD_ORGANISATION_FAILURE;
  error: string;
}

export type LoadOrganisationsAction =
  | LoadOrganisationsRequest
  | LoadOrganisationsSuccess
  | LoadOrganisationsFailure;
