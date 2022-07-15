import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";
import {
  CreditTransferActionTypes,
  ModifyCreditTransferActionTypes,
  LoadCreditTransferActionTypes
} from "./types";

import {
  CreditTransferAction,
  ModifyCreditTransferAction,
  LoadCreditTransferAction
} from "./actions";

export const byId = (state = {}, action: CreditTransferAction) => {
  switch (action.type) {
    case CreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST:
      if (!action.payload) {
        return {};
      }
      Object.keys(action.payload).map(id => {
        let transfer = action.payload[id];
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
      return DEEEEEEP({}, action.payload);
    default:
      return state;
  }
};

interface RequestingState {
  isRequesting: boolean;
  success: boolean;
  error: null | string;
}

const initialState: RequestingState = {
  isRequesting: false,
  success: false,
  error: null
};

const loadStatus = (
  state = initialState,
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
        data: action.payload.data,
        success: true
      };
    case ModifyCreditTransferActionTypes.MODIFY_TRANSFER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const createStatus = (
  state = initialState,
  action: CreditTransferAction
): RequestingState => {
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

export interface Pagination {
  items: number;
}

const initialPaginationState: Pagination = {
  items: 0
};

const pagination = (
  state = initialPaginationState,
  action: LoadCreditTransferAction
) => {
  switch (action.type) {
    case LoadCreditTransferActionTypes.UPDATE_CREDIT_TRANSFER_LIST_PAGINATION:
      return { items: action.payload };
    default:
      return state;
  }
};

export const creditTransfers = combineReducers({
  byId,
  createStatus,
  modifyStatus,
  loadStatus,
  pagination
});
