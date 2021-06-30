import { createAction, ActionsUnion } from "../../reduxUtils";
import {
  CreditTransfers,
  CreditTransferActionTypes,
  ModifyCreditTransferActionTypes,
  ModifyCreditTransferRequestPayload,
  CreateCreditTransferPayload,
  ModifyCreditTransferPayload,
  NewLoadTransferAccountListPayload,
  LoadCreditTransferActionTypes
} from "./types";

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

export const loadCreditTransferRequest = (
  payload: NewLoadTransferAccountListPayload
) =>
  createAction(
    LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST,
    payload
  );

export const updateCreditTransferListRequest = (
  credit_transfers: CreditTransfers
) =>
  createAction(
    CreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST,
    credit_transfers
  );

export const loadCreditTransferSuccess = () =>
  createAction(LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_SUCCESS);

export const loadCreditTransferFailure = (error: string) =>
  createAction(
    LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_FAILURE,
    error
  );

export const updateCreditTransferPagination = (items: number) =>
  createAction(
    LoadCreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST_PAGINATION,
    items
  );

export const LoadCreditTransferAction = {
  loadCreditTransferRequest,
  loadCreditTransferSuccess,
  loadCreditTransferFailure,
  updateCreditTransferPagination,
  updateCreditTransferListRequest
};

export type LoadCreditTransferAction = ActionsUnion<
  typeof LoadCreditTransferAction
>;
