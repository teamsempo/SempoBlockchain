import {
  TransferAccountActionTypes,
  LoadTransferAccountActionTypes,
  EditTransferAccountActionTypes,
  SetTransferAccountActionTypes,
  TransfersByUserId,
  LoadTransferAccountListPayload,
  EditTransferAccountPayload,
  TransferAccountIdList
} from "./types";
import { CreditTransfer } from "../creditTransfer/types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const setSelected = (selected: string[]) =>
  createAction(SetTransferAccountActionTypes.SET_SELECTED, selected);

export const resetSelected = () =>
  createAction(SetTransferAccountActionTypes.RESET_SELECTED);

export const SetTransferAccountAction = {
  setSelected,
  resetSelected
};

export type SetTransferAccountAction = ActionsUnion<
  typeof SetTransferAccountAction
>;

export const updateTransferAccountIdList = (IdList: TransferAccountIdList) =>
  createAction(
    TransferAccountActionTypes.UPDATE_TRANSFER_ACCOUNT_ID_LIST,
    IdList
  );

export const deepUpdateTransferAccounts = (
  transfer_accounts: TransfersByUserId
) =>
  createAction(
    TransferAccountActionTypes.DEEP_UPDATE_TRANSFER_ACCOUNTS,
    transfer_accounts
  );

export const updateTransferAccounts = (transfer_accounts: TransfersByUserId) =>
  createAction(
    TransferAccountActionTypes.UPDATE_TRANSFER_ACCOUNTS,
    transfer_accounts
  );

export const updateTransferAccountsCreditTransfers = (
  credit_transfer_list: CreditTransfer[]
) =>
  createAction(
    TransferAccountActionTypes.UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS,
    credit_transfer_list
  );

export const TransferAccountAction = {
  updateTransferAccountIdList,
  deepUpdateTransferAccounts,
  updateTransferAccounts,
  updateTransferAccountsCreditTransfers
};

export type TransferAccountAction = ActionsUnion<typeof TransferAccountAction>;

export const loadTransferAccountsRequest = (
  payload: LoadTransferAccountListPayload
) =>
  createAction(
    LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_REQUEST,
    payload
  );

export const loadTransferAccountsSuccess = (lastQueried: Date) =>
  createAction(
    LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_SUCCESS,
    lastQueried
  );

export const loadTransferAccountsFailure = (error: any) =>
  createAction(
    LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_FAILURE,
    error
  );

export const LoadTransferAccountAction = {
  loadTransferAccountsRequest,
  loadTransferAccountsSuccess,
  loadTransferAccountsFailure
};

export type LoadTransferAccountAction = ActionsUnion<
  typeof LoadTransferAccountAction
>;

export const editTransferAccountRequest = (
  payload: EditTransferAccountPayload
) =>
  createAction(
    EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_REQUEST,
    payload
  );

export const editTransferAccountSuccess = () =>
  createAction(EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_SUCCESS);

export const editTransferAccountFailure = (error: any) =>
  createAction(
    EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_FAILURE,
    error
  );

export const EditTransferAccountAction = {
  editTransferAccountRequest,
  editTransferAccountSuccess,
  editTransferAccountFailure
};

export type EditTransferAccountAction = ActionsUnion<
  typeof EditTransferAccountAction
>;
