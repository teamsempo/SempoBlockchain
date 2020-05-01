import { combineReducers } from "redux";
import {
  LoadTransferUsagesActionTypes,
  TransferUsageActionTypes,
  TransferUsage
} from "./types";
import { TransferUsageAction, LoadTransferUsagesAction } from "./actions";

const transferUsages = (
  state: TransferUsage[] = [],
  action: TransferUsageAction
): TransferUsage[] => {
  switch (action.type) {
    case TransferUsageActionTypes.UPDATE_TRANSFER_USAGES:
      return action.payload;

    default:
      return state;
  }
};

interface LoadTransferUsageState {
  isRequesting: boolean;
  error?: string;
  success: boolean;
}
const initialLoadStatusState = {
  isRequesting: false,
  success: false
};
const loadStatus = (
  state = initialLoadStatusState,
  action: LoadTransferUsagesAction
): LoadTransferUsageState => {
  switch (action.type) {
    case LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_REQUEST:
      return { ...state, isRequesting: true };

    case LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const TransferUsageReducer = combineReducers({
  transferUsages,
  loadStatus
});
