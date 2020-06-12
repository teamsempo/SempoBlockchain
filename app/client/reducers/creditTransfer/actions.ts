import { createAction, ActionsUnion } from "../../reduxUtils";
import {
  CreditTransfer,
  CreditTransfers,
  CreditTransferActionTypes,
  LoadCreditTransferActionTypes,
  ModifyCreditTransferActionTypes
} from "./types";

// ACTIONS
export const loadCreditTransferListRequest = () => ({
  type: LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST as typeof LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST
});

export const loadCreditTransferListSuccess = () => ({
  type: LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_SUCCESS as typeof LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_SUCCESS
});

export const loadCreditTransferListFailure = (err: any) => ({
  type: LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_FAILURE as typeof LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_FAILURE,
  error: err
});

export const LoadCreditTransferAction = {
  loadCreditTransferListRequest,
  loadCreditTransferListSuccess,
  loadCreditTransferListFailure
};

export type LoadCreditTransferAction = ActionsUnion<
  typeof LoadCreditTransferAction
>;

export const modifyTransferRequest = () => ({
  type: ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST as typeof ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST
});

export const modifyTransferSuccess = (result: any) => ({
  type: ModifyCreditTransferActionTypes.MODIFY_TRANSFER_SUCCESS as typeof ModifyCreditTransferActionTypes.MODIFY_TRANSFER_SUCCESS,
  result
});

export const modifyTransferFailure = (error: any) => ({
  type: ModifyCreditTransferActionTypes.MODIFY_TRANSFER_FAILURE as typeof ModifyCreditTransferActionTypes.MODIFY_TRANSFER_FAILURE,
  error
});

export const ModifyCreditTransferAction = {
  modifyTransferRequest,
  modifyTransferSuccess,
  modifyTransferFailure
};

export type ModifyCreditTransferAction = ActionsUnion<
  typeof ModifyCreditTransferAction
>;

export const createTransferRequest = (payload: any) => ({
  type: CreditTransferActionTypes.CREATE_TRANSFER_REQUEST as typeof CreditTransferActionTypes.CREATE_TRANSFER_REQUEST,
  payload
});

export const createTransferSuccess = () => ({
  type: CreditTransferActionTypes.CREATE_TRANSFER_SUCCESS as typeof CreditTransferActionTypes.CREATE_TRANSFER_SUCCESS
});

export const createTransferFailure = (error: any) => ({
  type: CreditTransferActionTypes.CREATE_TRANSFER_FAILURE as typeof CreditTransferActionTypes.CREATE_TRANSFER_FAILURE,
  error
});

export const updateCreditTransferListRequest = (
  credit_transfers: CreditTransfers
) => ({
  type: CreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST as typeof CreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST,
  credit_transfers
});

export const CreditTransferAction = {
  createTransferRequest,
  createTransferSuccess,
  createTransferFailure,
  updateCreditTransferListRequest
};

export type CreditTransferAction = ActionsUnion<typeof CreditTransferAction>;
