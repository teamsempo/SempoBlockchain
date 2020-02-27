import { combineReducers } from "redux";
import {
  LOAD_TRANSFER_USAGES_FAILURE,
  LOAD_TRANSFER_USAGES_REQUEST,
  LOAD_TRANSFER_USAGES_SUCCESS,
  LoadTransferUsagesAction,
  UPDATE_TRANSFER_USAGES,
  TransferUsagesAction,
  TransferUsage
} from "./types";

const transferUsages = (
  state: TransferUsage[] = [],
  action: TransferUsagesAction
): TransferUsage[] => {
  switch (action.type) {
    case UPDATE_TRANSFER_USAGES:
      return action.transferUsages;

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
    case LOAD_TRANSFER_USAGES_REQUEST:
      return { ...state, isRequesting: true };

    case LOAD_TRANSFER_USAGES_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LOAD_TRANSFER_USAGES_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const TransferUsageReducer = combineReducers({
  transferUsages,
  loadStatus
});
