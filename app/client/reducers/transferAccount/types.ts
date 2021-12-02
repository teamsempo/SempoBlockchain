import * as React from "react";

export interface TransferAccount {
  id: string;
}

export interface TransferAccountByIDs {
  [key: number]: TransferAccount;
}

export enum TransferAccountActionTypes {
  UPDATE_TRANSFER_ACCOUNT_PAGINATION = "UPDATE_TRANSFER_ACCOUNT_PAGINATION",
  DEEP_UPDATE_TRANSFER_ACCOUNTS = "DEEP_UPDATE_TRANSFER_ACCOUNTS",
  UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS = "UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS",
  UPDATE_TRANSFER_ACCOUNTS = "UPDATE_TRANSFER_ACCOUNTS",
  UPDATE_TRANSFER_ACCOUNT_ID_LIST = "UPDATE_TRANSFER_ACCOUNT_ID_LIST"
}

export enum LoadTransferAccountActionTypes {
  LOAD_TRANSFER_ACCOUNTS_REQUEST = "LOAD_TRANSFER_ACCOUNTS_REQUEST",
  LOAD_TRANSFER_ACCOUNTS_SUCCESS = "LOAD_TRANSFER_ACCOUNTS_SUCCESS",
  LOAD_TRANSFER_ACCOUNTS_FAILURE = "LOAD_TRANSFER_ACCOUNTS_FAILURE",
  LOAD_TRANSFER_ACCOUNT_HISTORY_REQUEST = "LOAD_TRANSFER_ACCOUNT_HISTORY_REQUEST"
}

export enum LoadTransferAccountHistoryActionTypes {
  LOAD_TRANSFER_ACCOUNT_HISTORY_REQUEST = "LOAD_TRANSFER_ACCOUNT_HISTORY_REQUEST",
  LOAD_TRANSFER_ACCOUNT_HISTORY_SUCCESS = "LOAD_TRANSFER_ACCOUNT_HISTORY_SUCCESS",
  LOAD_TRANSFER_ACCOUNT_HISTORY_FAILURE = "LOAD_TRANSFER_ACCOUNT_HISTORY_FAILURE"
}

export enum EditTransferAccountActionTypes {
  EDIT_TRANSFER_ACCOUNT_REQUEST = "EDIT_TRANSFER_ACCOUNT_REQUEST",
  EDIT_TRANSFER_ACCOUNT_SUCCESS = "EDIT_TRANSFER_ACCOUNT_SUCCESS",
  EDIT_TRANSFER_ACCOUNT_FAILURE = "EDIT_TRANSFER_ACCOUNT_FAILURE"
}

export enum SetTransferAccountActionTypes {
  SET_SELECTED = "SET_SELECTED",
  RESET_SELECTED = "RESET_SELECTED"
}

export interface SingularTransferAccountData {
  transfer_account: string;
}

export interface MultipleTransferAccountData {
  transfer_accounts: string[];
}

export type TransferAccountData =
  | SingularTransferAccountData
  | MultipleTransferAccountData;

export interface TransferAccountLoadApiResult {
  type: typeof LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_REQUEST;
  payload: any;
}

export interface TransferAccountLoadHistoryApiResult {
  type: typeof LoadTransferAccountHistoryActionTypes.LOAD_TRANSFER_ACCOUNT_HISTORY_REQUEST;
  payload: any;
}
export interface TransferAccountEditApiResult {
  type: typeof EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_REQUEST;
  payload: any;
}

interface TransfersForUser {
  credit_sends: string[]; // ids
  credit_receives: string[];
}

export interface TransfersByUserId {
  [userId: number]: TransfersForUser;
}

export interface LoadTransferAccountListPayload {
  query?: {};
  path?: number;
}

export interface LoadTransferAccountHistoryPayload {
  query?: {};
  path?: number;
}

export interface EditTransferAccountPayload {
  body: {
    params?: string;
    search_string?: string;
    include_accounts?: React.Key[];
    exclude_accounts?: React.Key[];
    transfer_account_id_list?: (string | number)[];
    approve?: boolean;
    balance?: number;
    nfc_card_id?: string;
    payable_period_length?: number;
    payable_period_type?: string;
    phone?: string;
    qr_code?: string;
  };
  path?: number | string;
}
