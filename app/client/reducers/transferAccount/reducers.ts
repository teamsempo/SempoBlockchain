import { combineReducers } from "redux";
import { DEEEEEEP, addCreditTransferIdsToTransferAccount } from "../../utils";

import {
  TransferAccountActionTypes,
  LoadTransferAccountActionTypes,
  EditTransferAccountActionTypes,
  SetTransferAccountActionTypes,
  TransfersByUserId
} from "./types";
import {
  TransferAccountAction,
  LoadTransferAccountAction,
  EditTransferAccountAction,
  SetTransferAccountAction
} from "./actions";

import {
  CreditTransfer,
  DisbursementCreditTransfer,
  ReclamationCreditTransfer
} from "../creditTransfer/types";

const initialByIdState: TransfersByUserId = {};

const byId = (state = initialByIdState, action: TransferAccountAction) => {
  switch (action.type) {
    case TransferAccountActionTypes.DEEP_UPDATE_TRANSFER_ACCOUNTS:
      return DEEEEEEP(state, action.payload);

    case TransferAccountActionTypes.UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS:
      var newState = {};

      action.payload.map((transfer: CreditTransfer) => {
        if (transfer.transfer_subtype === "DISBURSEMENT") {
          let updatedTransferAccount = {
            [(transfer as DisbursementCreditTransfer).recipient_transfer_account
              .id]: {
              credit_receives: [transfer.id]
            }
          };
          newState = { ...newState, ...updatedTransferAccount };
        } else if (transfer.transfer_subtype === "RECLAMATION") {
          let updatedTransferAccount = {
            [(transfer as ReclamationCreditTransfer).sender_transfer_account
              .id]: {
              credit_sends: [transfer.id]
            }
          };
          newState = { ...newState, ...updatedTransferAccount };
        }
      });

      return addCreditTransferIdsToTransferAccount(state, newState);

    case TransferAccountActionTypes.UPDATE_TRANSFER_ACCOUNTS:
      return action.payload;

    default:
      return state;
  }
};

interface LoadStatusState {
  isRequesting: boolean;
  error?: Error | null;
  success: Boolean;
  lastQueried?: Date | null;
}

const initialLoadStatusState: LoadStatusState = {
  isRequesting: false,
  error: null,
  success: false,
  lastQueried: null
};

const loadStatus = (
  state = initialLoadStatusState,
  action: LoadTransferAccountAction
) => {
  switch (action.type) {
    case LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_REQUEST:
      return { ...state, isRequesting: true };

    case LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        success: true,
        lastQueried: action.payload || state.lastQueried
      };

    case LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialEditStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const editStatus = (
  state = initialEditStatusState,
  action: EditTransferAccountAction
) => {
  switch (action.type) {
    case EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_REQUEST:
      return { ...state, isRequesting: true };

    case EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialSelectedState: any[] = [];

const selected = (
  state = initialSelectedState,
  action: SetTransferAccountAction
) => {
  switch (action.type) {
    case SetTransferAccountActionTypes.SET_SELECTED:
      return action.payload;
    case SetTransferAccountActionTypes.RESET_SELECTED:
      return initialSelectedState;

    default:
      return state;
  }
};

export const transferAccounts = combineReducers({
  byId,
  loadStatus,
  editStatus,
  selected
});
