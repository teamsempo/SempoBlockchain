export enum UserListActionTypes {
  DEEP_UPDATE_USER_LIST = "DEEP_UPDATE_USER_LIST",
  UPDATE_USER_LIST = "UPDATE_USER_LIST"
}

export interface User {
  id: number;
  phone: string;
  default_transfer_account_id: number;
  first_name: string;
  last_name: string;
  lat: null | string;
  lng: null | string;
  location: string;
  is_vendor: boolean;
  is_beneficiary: boolean;
  is_groupaccount: boolean;
  is_tokenagent: boolean;
  is_disabled: boolean;
  custom_attributes: object;
  public_serial_number: number;
  business_usage_name: string;
  referred_by: string;
  one_time_code?: string;
}

export enum LoadUserActionTypes {
  LOAD_USER_REQUEST = "LOAD_USER_REQUEST",
  LOAD_USER_SUCCESS = "LOAD_USER_SUCCESS",
  LOAD_USER_FAILURE = "LOAD_USER_FAILURE"
}

export interface LoadUserRequestPayload {
  query: {};
  path: number;
}

export enum EditUserActionTypes {
  EDIT_USER_REQUEST = "EDIT_USER_REQUEST",
  EDIT_USER_SUCCESS = "EDIT_USER_SUCCESS",
  EDIT_USER_FAILURE = "EDIT_USER_FAILURE"
}

export interface EditUserPayload {
  path: number;
  body: User
}

export enum CreateUserActionTypes {
  CREATE_USER_REQUEST = "CREATE_USER_REQUEST",
  CREATE_USER_SUCCESS = "CREATE_USER_SUCCESS",
  CREATE_USER_FAILURE = "CREATE_USER_FAILURE",
  RESET_CREATE_USER = "RESET_CREATE_USER"
}

export interface CreateUserPayload {
  body: User
}

export interface CreateUserSuccessPayload {
  data: {
    user: User
    message: string
  }
}

export enum DeleteUserActionTypes {
  DELETE_USER_REQUEST = "DELETE_USER_REQUEST",
  DELETE_USER_SUCCESS = "DELETE_USER_SUCCESS",
  DELETE_USER_FAILURE = "DELETE_USER_FAILURE"
}

export interface DeleteUserPayload {
  path: number
}

export enum ResetPinActionTypes {
  RESET_PIN_REQUEST = "RESET_PIN_REQUEST",
  RESET_PIN_SUCCESS = "RESET_PIN_SUCCESS",
  RESET_PIN_FAILURE = "RESET_PIN_FAILURE"
}

export interface ResetPinPayload {
  body: {
    user_id: number;
  }
}