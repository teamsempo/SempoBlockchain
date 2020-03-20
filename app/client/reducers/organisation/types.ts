export interface Organisation {
  id: number;
  name: string;
  token: {
    symbol: string;
  };
  require_transfer_card: boolean;
  default_disbursement: number;
  country_code: string;
}

export const UPDATE_ORGANISATION_LIST = 'UPDATE_ORGANISATION_LIST';

interface UpdateOrganisationList {
  type: typeof UPDATE_ORGANISATION_LIST;
  organisations: Organisation;
}

export type OrganisationAction = UpdateOrganisationList;

export const EDIT_ORGANISATION_REQUEST = 'EDIT_ORGANISATION_REQUEST';

export interface EditOrganisationPayload {
  body: {
    country_code: string;
    default_disbursement: number;
    require_transfer_card: boolean;
    default_lat: number;
    default_lng: number;
  };
  path: number;
}

interface EditOrganisationRequest {
  type: typeof EDIT_ORGANISATION_REQUEST;
  payload: EditOrganisationPayload;
}

export const EDIT_ORGANISATION_SUCCESS = 'EDIT_ORGANISATION_SUCCESS';

interface EditOrganisationSuccess {
  type: typeof EDIT_ORGANISATION_SUCCESS;
}

export const EDIT_ORGANISATION_FAILURE = 'EDIT_ORGANISATION_FAILURE';

interface EditOrganisationFailure {
  type: typeof EDIT_ORGANISATION_FAILURE;
  error: string;
}

export type EditOrganisationAction =
  | EditOrganisationRequest
  | EditOrganisationSuccess
  | EditOrganisationFailure;

export const LOAD_ORGANISATION_REQUEST = 'LOAD_ORGANISATIONS_REQUEST';

interface LoadOrganisationsRequest {
  type: typeof LOAD_ORGANISATION_REQUEST;
}
export const LOAD_ORGANISATION_SUCCESS = 'LOAD_ORGANISATIONS_SUCCESS';

interface LoadOrganisationsSuccess {
  type: typeof LOAD_ORGANISATION_SUCCESS;
}
export const LOAD_ORGANISATION_FAILURE = 'LOAD_ORGANISATIONS_FAILURE';

interface LoadOrganisationsFailure {
  type: typeof LOAD_ORGANISATION_FAILURE;
  error: string;
}

export type LoadOrganisationsAction =
  | LoadOrganisationsRequest
  | LoadOrganisationsSuccess
  | LoadOrganisationsFailure;
