import { DEEEEEEP } from "../../utils";
import { combineReducers } from "redux";
import { WyreActionTypes, WyreState } from "./types";
import { WyreAction } from "./actions";

const initalWyreState: WyreState = {
  wyre_rates: null,
  wyre_account: null,
  wyre_transfer: null
};

const wyreState = (state: WyreState = initalWyreState, action: WyreAction) => {
  switch (action.type) {
    case WyreActionTypes.UPDATE_WYRE_STATE:
      return DEEEEEEP(state, action.payload);
    default:
      return state;
  }
};

const initialLoadWyreExchangeStatus = {
  isRequesting: false,
  error: null,
  success: false
};

const loadWyreExchangeStatus = (
  state = initialLoadWyreExchangeStatus,
  action: WyreAction
) => {
  switch (action.type) {
    case WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_REQUEST:
      return { ...state, isRequesting: true };
    case WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

export const initialLoadWyreAccountStatus = {
  isRequesting: false,
  error: null,
  success: false
};

export const loadWyreAccountStatus = (
  state = initialLoadWyreAccountStatus,
  action: WyreAction
) => {
  switch (action.type) {
    case WyreActionTypes.LOAD_WYRE_ACCOUNT_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case WyreActionTypes.LOAD_WYRE_ACCOUNT_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case WyreActionTypes.LOAD_WYRE_ACCOUNT_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

export const initialCreateWyreTransferStatus = {
  isRequesting: false,
  error: null,
  success: false
};

export const createWyreTransferStatus = (
  state = initialCreateWyreTransferStatus,
  action: WyreAction
) => {
  switch (action.type) {
    case WyreActionTypes.CREATE_WYRE_TRANSFER_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case WyreActionTypes.CREATE_WYRE_TRANSFER_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case WyreActionTypes.CREATE_WYRE_TRANSFER_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

export const wyre = combineReducers({
  wyreState,
  loadWyreExchangeStatus,
  loadWyreAccountStatus,
  createWyreTransferStatus
});
