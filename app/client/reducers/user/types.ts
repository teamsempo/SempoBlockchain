import { TransferAccountTypes } from "../../components/transferAccount/types";

export enum UserListActionTypes {
  REPLACE_USER_LIST = "REPLACE_USER_LIST", //Replaces the existing user list with the new one supplied
  UPDATE_USER_LIST = "UPDATE_USER_LIST", //Updates the existing user list by merging with the new one, overwriting new user data on a collision
  DEEP_UPDATE_USER_LIST = "DEEP_UPDATE_USER_LIST" //Updates the existing user list by merging with the new one, merging user data as well
}

export interface User {
  id?: number;
  phone?: string;
  default_transfer_account_id?: number;
  first_name?: string;
  last_name?: string;
  lat?: string;
  lng?: string;
  location?: string;
  is_vendor?: boolean;
  is_disabled?: boolean;
  custom_attributes?: object;
  public_serial_number?: string;
  business_usage_name?: string;
  referred_by?: string;
  one_time_code?: string;
  account_types?: string[];
}

export interface CreateUser extends User {
  bio?: string;
  gender?: string;
  initial_disbursement?: number;
  require_transfer_card_exists?: boolean;
  require_multiple_transfer_approvals?: boolean;
  existing_vendor_phone?: string;
  existing_vendor_pin?: string;
  transfer_account_name?: string;
}

export interface UserData {
  user: User;
  users: User[];
}

export enum LoadUserActionTypes {
  LOAD_USER_REQUEST = "LOAD_USER_REQUEST",
  LOAD_USER_SUCCESS = "LOAD_USER_SUCCESS",
  LOAD_USER_FAILURE = "LOAD_USER_FAILURE"
}

export interface LoadUserRequestPayload {
  query?: {};
  path: number;
}

export enum EditUserActionTypes {
  EDIT_USER_REQUEST = "EDIT_USER_REQUEST",
  EDIT_USER_SUCCESS = "EDIT_USER_SUCCESS",
  EDIT_USER_FAILURE = "EDIT_USER_FAILURE"
}

export interface EditUserPayload {
  path: number;
  body: User;
}

export enum CreateUserActionTypes {
  CREATE_USER_REQUEST = "CREATE_USER_REQUEST",
  CREATE_USER_SUCCESS = "CREATE_USER_SUCCESS",
  CREATE_USER_FAILURE = "CREATE_USER_FAILURE",
  RESET_CREATE_USER = "RESET_CREATE_USER"
}

export interface CreateUserPayload {
  body: CreateUser;
}

export interface CreateUserSuccessPayload {
  data: {
    user: User;
    message: string;
  };
}

export enum DeleteUserActionTypes {
  DELETE_USER_REQUEST = "DELETE_USER_REQUEST",
  DELETE_USER_SUCCESS = "DELETE_USER_SUCCESS",
  DELETE_USER_FAILURE = "DELETE_USER_FAILURE"
}

export interface DeleteUserPayload {
  path: number;
}

export enum ResetPinActionTypes {
  RESET_PIN_REQUEST = "RESET_PIN_REQUEST",
  RESET_PIN_SUCCESS = "RESET_PIN_SUCCESS",
  RESET_PIN_FAILURE = "RESET_PIN_FAILURE"
}

export interface ResetPinPayload {
  body: {
    user_id: number;
  };
}

export interface UserByIDs {
  [key: number]: User;
}
