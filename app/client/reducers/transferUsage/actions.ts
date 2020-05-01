import {
  LoadTransferUsagePayload,
  TransferUsage,
  TransferUsageActionTypes,
  LoadTransferUsagesActionTypes
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const TransferUsageAction = {
  updateTransferUsages: (transferUsages: TransferUsage[]) =>
    createAction(
      TransferUsageActionTypes.UPDATE_TRANSFER_USAGES,
      transferUsages
    )
};
export type TransferUsageAction = ActionsUnion<typeof TransferUsageAction>;

export const LoadTransferUsagesAction = {
  loadTransferUsagesRequest: (payload: LoadTransferUsagePayload) =>
    createAction(
      LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_REQUEST,
      payload
    ),
  loadTransferUsagesSuccess: () =>
    createAction(LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_SUCCESS),
  loadTransferUsagesFailure: (error: string) =>
    createAction(
      LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_FAILURE,
      error
    )
};
export type LoadTransferUsagesAction = ActionsUnion<
  typeof LoadTransferUsagesAction
>;
