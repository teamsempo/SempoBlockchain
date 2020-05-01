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

export enum OrganisationActionTypes {
  UPDATE_ORGANISATION_LIST = "UPDATE_ORGANISATION_LIST"
}

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

export enum EditOrganisationActionTypes {
  EDIT_ORGANISATION_REQUEST = "EDIT_ORGANISATION_REQUEST",
  EDIT_ORGANISATION_SUCCESS = "EDIT_ORGANISATION_SUCCESS",
  EDIT_ORGANISATION_FAILURE = "EDIT_ORGANISATION_FAILURE"
}

export enum LoadOrganisationActionTypes {
  LOAD_ORGANISATION_REQUEST = "LOAD_ORGANISATION_REQUEST",
  LOAD_ORGANISATION_SUCCESS = "LOAD_ORGANISATION_SUCCESS",
  LOAD_ORGANISATION_FAILURE = "LOAD_ORGANISATION_FAILURE"
}
