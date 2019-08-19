import { DEEEEEEP } from "../utils";
import { combineReducers } from "redux";

export const UPDATE_WYRE_STATE = 'UPDATE_WYRE_STATE';

export const LOAD_WYRE_EXCHANGE_RATES_REQUEST = 'LOAD_WYRE_EXCHANGE_RATES_REQUEST';
export const LOAD_WYRE_EXCHANGE_RATES_SUCCESS = 'LOAD_WYRE_EXCHANGE_RATES_SUCCESS';
export const LOAD_WYRE_EXCHANGE_RATES_FAILURE = 'LOAD_WYRE_EXCHANGE_RATES_FAILURE';

export const LOAD_WYRE_ACCOUNT_REQUEST = 'LOAD_WYRE_ACCOUNT_REQUEST';
export const LOAD_WYRE_ACCOUNT_SUCCESS = 'LOAD_WYRE_ACCOUNT_SUCCESS';
export const LOAD_WYRE_ACCOUNT_FAILURE = 'LOAD_WYRE_ACCOUNT_FAILURE';

export const CREATE_WYRE_TRANSFER_REQUEST = 'CREATE_WYRE_TRANSFER_REQUEST';
export const CREATE_WYRE_TRANSFER_SUCCESS = 'CREATE_WYRE_TRANSFER_SUCCESS';
export const CREATE_WYRE_TRANSFER_FAILURE = 'CREATE_WYRE_TRANSFER_FAILURE';


const initalWyreState = {
  wyre_rates: null,
  wyre_account: null,
  wyre_transfer: null,
};

const wyreState = (state = initalWyreState, action) => {
  switch (action.type) {
    case UPDATE_WYRE_STATE:
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

const loadWyreExchangeStatus = (state = initialLoadWyreExchangeStatus, action) => {
  switch (action.type) {
    case LOAD_WYRE_EXCHANGE_RATES_REQUEST:
      return {...state, isRequesting: true};
    case LOAD_WYRE_EXCHANGE_RATES_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case LOAD_WYRE_EXCHANGE_RATES_FAILURE:
      return {...state, isRequesting: false, error: action.error};
    default:
      return state;
  }
};


export const initialLoadWyreAccountStatus = {
  isRequesting: false,
  error: null,
  success: false,
};

export const loadWyreAccountStatus = (state = initialLoadWyreAccountStatus, action) => {
  switch (action.type) {
    case LOAD_WYRE_ACCOUNT_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case LOAD_WYRE_ACCOUNT_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case LOAD_WYRE_ACCOUNT_FAILURE:
      return {...state, isRequesting: false, error: action.error};
    default:
      return state;
  }
};

export const initialCreateWyreTransferStatus = {
  isRequesting: false,
  error: null,
  success: false,
};

export const createWyreTransferStatus = (state = initialCreateWyreTransferStatus, action) => {
  switch (action.type) {
    case CREATE_WYRE_TRANSFER_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case CREATE_WYRE_TRANSFER_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case CREATE_WYRE_TRANSFER_FAILURE:
      return {...state, isRequesting: false, error: action.error};
    default:
      return state;
  }
};


export const wyre = combineReducers({
  wyreState,
  loadWyreExchangeStatus,
  loadWyreAccountStatus,
  createWyreTransferStatus,
});


// Actions
export const loadExchangeRates = (payload) => (
  {
    type: LOAD_WYRE_EXCHANGE_RATES_REQUEST,
    payload
  }
);

export const loadWyreAccountBalance = (payload) => (
  {
    type: LOAD_WYRE_ACCOUNT_REQUEST,
    payload
  }
);

export const createWyreTransfer = (payload) => (
  {
    type: CREATE_WYRE_TRANSFER_REQUEST,
    payload
  }
);
