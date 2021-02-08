import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";
import {
  BulkTransferActionTypes,
  BulkTransfersById,
  CreateBulkTransferActionTypes
} from "./types";

import { BulkTransferListAction, CreateBulkTransferAction } from "./actions";
import { UserListAction } from "../user/actions";

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

export const createStatus = (
  state = initialState,
  action: CreateBulkTransferAction
): RequestingState => {
  switch (action.type) {
    case CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const byId = (
  state: BulkTransfersById = {},
  action: BulkTransferListAction
) => {
  switch (action.type) {
    case BulkTransferActionTypes.DEEP_UPDATE_BULK_TRANSFERS:
      return DEEEEEEP(state, action.payload);
    default:
      return state;
  }
};

export const bulkTransfers = combineReducers({
  createStatus,
  byId
});
