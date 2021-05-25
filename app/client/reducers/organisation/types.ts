import { TransferAccountTypes } from "../../components/transferAccount/types";

export interface Organisation {
  id: number;
  name: string;
  token: number;
  require_transfer_card: boolean;
  default_disbursement: number;
  card_shard_distance: number;
  minimum_vendor_payout_withdrawal: number;
  master_wallet_balance: number;
  country_code: string;
  timezone: string;
  valid_roles: TransferAccountTypes[];
}

export interface OrganisationByIDs {
  [key: number]: Organisation;
}

export interface OrganisationData {
  organisations: Organisation[];
  organisation: Organisation;
}

export enum OrganisationActionTypes {
  UPDATE_ORGANISATION_LIST = "UPDATE_ORGANISATION_LIST"
}

export interface EditOrganisationPayload {
  body: {
    country_code: string;
    timezone: string;
    default_disbursement: number;
    card_shard_distance: number;
    minimum_vendor_payout_withdrawal: number;
    require_transfer_card: boolean;
    default_lat: number;
    default_lng: number;
  };
  path: number;
}

export interface CreateOrganisationPayload {
  body: {
    name: string;
    token_id: number;
    require_transfer_card: boolean;
    default_disbursement: number;
    card_shard_distance: number;
    minimum_vendor_payout_withdrawal: number;
    country_code: string;
    valid_roles: TransferAccountTypes[];
  };
}

export enum CreateOrganisationActionTypes {
  CREATE_ORGANISATION_REQUEST = "CREATE_ORGANISATION_REQUEST",
  CREATE_ORGANISATION_SUCCESS = "CREATE_ORGANISATION_SUCCESS",
  CREATE_ORGANISATION_FAILURE = "CREATE_ORGANISATION_FAILURE"
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
