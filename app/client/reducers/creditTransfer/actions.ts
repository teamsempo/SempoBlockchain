import { createAction, ActionsUnion } from "../../reduxUtils";
import {
  CreditTransfers,
  CreditTransferActionTypes,
  LoadCreditTransferActionTypes,
  ModifyCreditTransferActionTypes,
  LoadCreditTransferPayload,
  ModifyCreditTransferRequestPayload,
  CreateCreditTransferPayload,
  ModifyCreditTransferPayload,
  NewLoadTransferAccountListPayload,
  NewLoadCreditTransferActionTypes
} from "./types";

export const LoadCreditTransferAction = {
  loadCreditTransferListRequest: (payload: LoadCreditTransferPayload) =>
    createAction(
      LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST,
      payload
    ),
  loadCreditTransferListSuccess: () =>
    createAction(
      LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_SUCCESS
    ),
  loadCreditTransferListFailure: (err: string) =>
    createAction(
      LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_FAILURE,
      err
    )
};

export type LoadCreditTransferAction = ActionsUnion<
  typeof LoadCreditTransferAction
>;

export const ModifyCreditTransferAction = {
  modifyTransferRequest: (payload: ModifyCreditTransferRequestPayload) =>
    createAction(
      ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST,
      payload
    ),
  modifyTransferSuccess: (payload: ModifyCreditTransferPayload) =>
    createAction(
      ModifyCreditTransferActionTypes.MODIFY_TRANSFER_SUCCESS,
      payload
    ),
  modifyTransferFailure: (err: string) =>
    createAction(ModifyCreditTransferActionTypes.MODIFY_TRANSFER_FAILURE, err)
};

export type ModifyCreditTransferAction = ActionsUnion<
  typeof ModifyCreditTransferAction
>;

export const CreditTransferAction = {
  createTransferRequest: (payload: CreateCreditTransferPayload) =>
    createAction(CreditTransferActionTypes.CREATE_TRANSFER_REQUEST, payload),
  createTransferSuccess: () =>
    createAction(CreditTransferActionTypes.CREATE_TRANSFER_SUCCESS),
  createTransferFailure: (err: string) =>
    createAction(CreditTransferActionTypes.CREATE_TRANSFER_FAILURE, err),
  updateCreditTransferListRequest: (credit_transfers: CreditTransfers) =>
    createAction(
      CreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST,
      credit_transfers
    )
};

export type CreditTransferAction = ActionsUnion<typeof CreditTransferAction>;


export const newLoadCreditTransferRequest = (
  payload: NewLoadTransferAccountListPayload
) =>
  createAction(
    NewLoadCreditTransferActionTypes.NEW_LOAD_CREDIT_TRANSFER_LIST_REQUEST,
    payload
  );

export const newLoadCreditTransferSuccess = (lastQueried: Date) =>
  createAction(
    NewLoadCreditTransferActionTypes.NEW_LOAD_CREDIT_TRANSFER_LIST_SUCCESS,
    lastQueried
  );

export const newLoadCreditTransferFailure = (error: string) =>
  createAction(
    NewLoadCreditTransferActionTypes.NEW_LOAD_CREDIT_TRANSFER_LIST_FAILURE,
    error
  );

export const NewLoadCreditTransferAction = {
  newLoadCreditTransferRequest,
  newLoadCreditTransferSuccess,
  newLoadCreditTransferFailure
};

export type NewLoadCreditTransferAction = ActionsUnion<
  typeof NewLoadCreditTransferAction
>;