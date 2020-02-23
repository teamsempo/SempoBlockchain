import { combineReducers } from "redux";
import { DEEEEEEP } from "../utils";

export const UPDATE_CREDIT_TRANSFER_LIST = "UPDATE_CREDIT_TRANSFER_LIST";

export const LOAD_CREDIT_TRANSFER_STATS_REQUEST =
  "LOAD_CREDIT_TRANSFER_STATS_REQUEST";
export const LOAD_CREDIT_TRANSFER_STATS_SUCCESS =
  "LOAD_CREDIT_TRANSFER_STATS_SUCCESS";
export const LOAD_CREDIT_TRANSFER_STATS_ERROR =
  "LOAD_CREDIT_TRANSFER_STATS_ERROR";
export const UPDATE_CREDIT_TRANSFER_STATS = "UPDATE_CREDIT_TRANSFER_STATS";

export const LOAD_CREDIT_TRANSFER_LIST_REQUEST =
  "LOAD_CREDIT_TRANSFER_LIST_REQUEST";
export const LOAD_CREDIT_TRANSFER_LIST_SUCCESS =
  "LOAD_CREDIT_TRANSFER_LIST_SUCCESS";
export const LOAD_CREDIT_TRANSFER_LIST_FAILURE =
  "LOAD_CREDIT_TRANSFER_LIST_FAILURE";
export const PUSHER_CREDIT_TRANSFER = "PUSHER_CREDIT_TRANSFER";

export const MODIFY_TRANSFER_REQUEST = "MODIFY_TRANSFER_REQUEST";
export const MODIFY_TRANSFER_SUCCESS = "MODIFY_TRANSFER_SUCCESS";
export const MODIFY_TRANSFER_FAILURE = "MODIFY_TRANSFER_FAILURE";

export const CREATE_TRANSFER_REQUEST = "CREATE_TRANSFER_REQUEST";
export const CREATE_TRANSFER_SUCCESS = "CREATE_TRANSFER_SUCCESS";
export const CREATE_TRANSFER_FAILURE = "CREATE_TRANSFER_FAILURE";

const byId = (state = {}, action) => {
  switch (action.type) {
    case UPDATE_CREDIT_TRANSFER_LIST:
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

const initialLoadStatState = {
  isRequesting: false,
  error: null,
  success: false
};

const transferStats = (state = initialLoadStatState, action) => {
  switch (action.type) {
    case LOAD_CREDIT_TRANSFER_STATS_REQUEST:
      return { ...state, isRequesting: true };
    case LOAD_CREDIT_TRANSFER_STATS_SUCCESS:
      return DEEEEEEP(
        { ...state, isRequesting: false, success: true },
        action.transferStats
      );
    case LOAD_CREDIT_TRANSFER_STATS_ERROR:
      return { ...state, isRequesting: false, error: action.error };
    case UPDATE_CREDIT_TRANSFER_STATS:
      return DEEEEEEP(state, action.transfer_stats);
    default:
      return state;
  }
};

const initialLoadStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const loadStatus = (state = initialLoadStatusState, action) => {
  switch (action.type) {
    case LOAD_CREDIT_TRANSFER_LIST_REQUEST:
      return { ...state, isRequesting: true };

    case LOAD_CREDIT_TRANSFER_LIST_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LOAD_CREDIT_TRANSFER_LIST_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const initialModifyStatusState = {
  isRequesting: false,
  error: null,
  success: null
};

export const modifyStatus = (state = initialModifyStatusState, action) => {
  switch (action.type) {
    case MODIFY_TRANSFER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case MODIFY_TRANSFER_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        data: action.result.data,
        success: true
      };
    case MODIFY_TRANSFER_FAILURE:
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

export const createStatus = (state = initialCreateStatusState, action) => {
  switch (action.type) {
    case CREATE_TRANSFER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case CREATE_TRANSFER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case CREATE_TRANSFER_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

export const creditTransfers = combineReducers({
  byId,
  transferStats,
  loadStatus,
  createStatus,
  modifyStatus
});

export const loadCreditTransferStats = payload => ({
  type: LOAD_CREDIT_TRANSFER_STATS_REQUEST,
  payload
});

// ACTIONS
export const loadCreditTransferList = payload => ({
  type: LOAD_CREDIT_TRANSFER_LIST_REQUEST,
  payload
});

export const modifyTransferRequest = payload => ({
  type: MODIFY_TRANSFER_REQUEST,
  payload
});

export const createTransferRequest = payload => ({
  type: CREATE_TRANSFER_REQUEST,
  payload
});
