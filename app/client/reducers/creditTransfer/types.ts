import { TransferAccount } from "../transferAccount/types";
import { User } from "../user/types";

export enum CreditTransferActionTypes {
  UPDATE_CREDIT_TRANSFER_LIST = "UPDATE_CREDIT_TRANSFER_LIST",
  PUSHER_CREDIT_TRANSFER = "PUSHER_CREDIT_TRANSFER",
  CREATE_TRANSFER_REQUEST = "CREATE_TRANSFER_REQUEST",
  CREATE_TRANSFER_SUCCESS = "CREATE_TRANSFER_SUCCESS",
  CREATE_TRANSFER_FAILURE = "CREATE_TRANSFER_FAILURE"
}

export enum LoadCreditTransferActionTypes {
  LOAD_CREDIT_TRANSFER_LIST_REQUEST = "LOAD_CREDIT_TRANSFER_LIST_REQUEST",
  LOAD_CREDIT_TRANSFER_LIST_SUCCESS = "LOAD_CREDIT_TRANSFER_LIST_SUCCESS",
  LOAD_CREDIT_TRANSFER_LIST_FAILURE = "LOAD_CREDIT_TRANSFER_LIST_FAILURE"
}

export enum NewLoadCreditTransferActionTypes {
  NEW_LOAD_CREDIT_TRANSFER_LIST_REQUEST = "NEW_LOAD_CREDIT_TRANSFER_LIST_REQUEST",
  NEW_LOAD_CREDIT_TRANSFER_LIST_SUCCESS = "NEW_LOAD_CREDIT_TRANSFER_LIST_SUCCESS",
  NEW_LOAD_CREDIT_TRANSFER_LIST_FAILURE = "NEW_LOAD_CREDIT_TRANSFER_LIST_FAILURE"
}

export enum ModifyCreditTransferActionTypes {
  MODIFY_TRANSFER_REQUEST = "MODIFY_TRANSFER_REQUEST",
  MODIFY_TRANSFER_SUCCESS = "MODIFY_TRANSFER_SUCCESS",
  MODIFY_TRANSFER_FAILURE = "MODIFY_TRANSFER_FAILURE"
}

export interface BaseCreditTransfer {
  attached_images?: object;
  authorising_user_email?: string;
  blockchain_status?: string;
  blockchain_task_uuid?: string;
  created?: string;
  id?: number;
  is_sender?: boolean;
  lat?: number;
  lng?: number;
  recipient_transfer_account?: TransferAccount;
  recipient_user?: User;
  resolved?: string;
  sender_transfer_account_id?: number;
  sender_user?: User;
  token?: {
    id: number;
    symbol: string;
  };
  transfer_amount: number;
  transfer_metadata?: null | object;
  transfer_status: string;
  transfer_subtype: string;
  transfer_type: string;
  transfer_use?: null | object;
  updated?: string;
  uuid?: null | string;
}

export interface DisbursementCreditTransfer extends BaseCreditTransfer {
  recipient_transfer_account: TransferAccount;
}

export interface ReclamationCreditTransfer extends BaseCreditTransfer {
  sender_transfer_account: TransferAccount;
}

export type CreditTransfer =
  | DisbursementCreditTransfer
  | ReclamationCreditTransfer;

  export interface NewCreditTransferLoadApiResult {
    type: typeof NewLoadCreditTransferActionTypes.NEW_LOAD_CREDIT_TRANSFER_LIST_REQUEST;
    payload: any;
  }

// TODO we should only need one of these keys
export interface CreditTransfers {
  [key: number]: CreditTransfer;

  [key: string]: CreditTransfer;
}
export interface NewLoadTransferAccountListPayload {
  query?: {};
  path?: number;
}
export interface LoadCreditTransferPayload {
  query?: {
    transfer_type: string;
    per_page: number;
    page: number;
  };
  path?: number;
}

export interface ModifyCreditTransferRequestPayload {
  body: {
    action: string;
  };
  path: number;
}

export interface ModifyCreditTransferPayload {
  data: CreditTransfer;
  message: string;
}

export interface CreateCreditTransferPayload {
  body: {
    is_bulk?: boolean;
    recipient_transfer_accounts_ids: object;
    transfer_amount: number;
    target_balance?: number;
    transfer_type: string;
  };
}
