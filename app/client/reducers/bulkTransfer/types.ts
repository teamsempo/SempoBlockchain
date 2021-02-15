import * as React from "react";
import {
  LoadTransferAccountActionTypes,
  TransferAccount
} from "../transferAccount/types";
import { User } from "../user/types";

export enum CreateBulkTransferActionTypes {
  CREATE_BULK_TRANSFER_REQUEST = "CREATE_BULK_TRANSFER_REQUEST",
  CREATE_BULK_TRANSFER_SUCCESS = "CREATE_BULK_TRANSFER_SUCCESS",
  CREATE_BULK_TRANSFER_FAILURE = "CREATE_BULK_TRANSFER_FAILURE"
}

export enum ModifyCreditTransferActionTypes {
  MODIFY_TRANSFER_REQUEST = "MODIFY_TRANSFER_REQUEST",
  MODIFY_TRANSFER_SUCCESS = "MODIFY_TRANSFER_SUCCESS",
  MODIFY_TRANSFER_FAILURE = "MODIFY_TRANSFER_FAILURE"
}

export enum LoadBulkTransfersActionTypes {
  LOAD_BULK_TRANSFERS_REQUEST = "LOAD_BULK_TRANSFERS_REQUEST",
  LOAD_BULK_TRANSFERS_SUCCESS = "LOAD_BULK_TRANSFERS_SUCCESS",
  LOAD_BULK_TRANSFERS_FAILURE = "LOAD_BULK_TRANSFERS_FAILURE"
}

export enum BulkTransferActionTypes {
  DEEP_UPDATE_BULK_TRANSFERS = "DEEP_UPDATE_TRANSFER_ACCOUNTS"
}

export interface LoadBulkTransferPayload {
  query?: {};
  path?: number;
}

export interface CreateBulkTransferBody {
  params?: string;
  search_string?: string;
  include_accounts?: React.Key[];
  exclude_accounts?: React.Key[];
  disbursement_amount: number;
  order?: "ASC" | "DESC";
}

export interface ModifyBulkTransferBody {
  action?: "COMPLETE" | "REJECT";
}

export interface CreateBulkTransferPayload {
  body: {
    params?: string;
    search_string?: string;
    include_accounts?: React.Key[];
    exclude_accounts?: React.Key[];
    disbursement_amount: number;
    order?: "ASC" | "DESC";
  };
}

export interface BulkTransferLoadApiResult {
  type: typeof LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_REQUEST;
  payload: any;
}

export interface BulkTransfersById {
  [key: number]: any;
}
