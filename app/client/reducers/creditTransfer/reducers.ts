import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";
import {
  CreditTransferActionTypes,
  LoadCreditTransferActionTypes,
  ModifyCreditTransferActionTypes
} from "./types";

import {
  CreditTransferAction,
  LoadCreditTransferAction,
  ModifyCreditTransferAction
} from "./actions";

export const byId = (state = {}, action: CreditTransferAction) => {
  switch (action.type) {
    case CreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST:
      Object.keys(action.credit_transfers).map(id => {
        let transfer = action.credit_transfers[id];
        if (
          transfer.transfer_subtype !== null &&
          typeof transfer.transfer_subtype !== "undefined"
        ) {
          if (transfer.transfer_subtype === "DISBURSEMENT") {
            transfer.transfer_type = "DISBURSEMENT";
          } else if (transfer.transfer_subtype === "RECLAMATION") {
            transfer.transfer_type = "RECLAMATION";
          }
        }
      });
      return DEEEEEEP(state, action.credit_transfers);
    default:
      return state;
  }
};

const initialLoadStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const loadStatus = (
  state = initialLoadStatusState,
  action: LoadCreditTransferAction
) => {
  switch (action.type) {
    case LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST:
      return { ...state, isRequesting: true };

    case LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialModifyStatusState: ModifyStatusState = {
  isRequesting: false,
  error: null,
  success: null
};

interface ModifyStatusState {
  isRequesting: boolean;
  error?: string | null;
  success: boolean | null;
  data?: any;
}

export const modifyStatus = (
  state = initialModifyStatusState,
  action: ModifyCreditTransferAction
): ModifyStatusState => {
  switch (action.type) {
    case ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case ModifyCreditTransferActionTypes.MODIFY_TRANSFER_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        data: action.result.data,
        success: true
      };
    case ModifyCreditTransferActionTypes.MODIFY_TRANSFER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const initialCreateStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const createStatus = (
  state = initialCreateStatusState,
  action: CreditTransferAction
) => {
  switch (action.type) {
    case CreditTransferActionTypes.CREATE_TRANSFER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case CreditTransferActionTypes.CREATE_TRANSFER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case CreditTransferActionTypes.CREATE_TRANSFER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const creditTransfers = combineReducers({
  byId,
  loadStatus,
  createStatus,
  modifyStatus
});
