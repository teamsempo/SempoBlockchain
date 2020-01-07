import { combineReducers } from 'redux';
import { DEEEEEEP, addCreditTransferIdsToTransferAccount } from '../utils'

export const UPDATE_TRANSFER_ACCOUNTS = "UPDATE_TRANSFER_ACCOUNTS";
export const UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS = "UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS";
export const UPDATE_TRANSFER_ACCOUNT_LIST_PAGINATION = 'UPDATE_TRANSFER_ACCOUNT_LIST_PAGINATION';

export const LOAD_TRANSFER_ACCOUNTS_REQUEST = "LOAD_TRANSFER_ACCOUNTS_REQUEST";
export const LOAD_TRANSFER_ACCOUNTS_SUCCESS = "LOAD_TRANSFER_ACCOUNTS_SUCCESS";
export const LOAD_TRANSFER_ACCOUNTS_FAILURE = "LOAD_TRANSFER_ACCOUNTS_FAILURE";

export const EDIT_TRANSFER_ACCOUNT_REQUEST = "EDIT_TRANSFER_ACCOUNT_REQUEST";
export const EDIT_TRANSFER_ACCOUNT_SUCCESS = "EDIT_TRANSFER_ACCOUNT_SUCCESS";
export const EDIT_TRANSFER_ACCOUNT_FAILURE = "EDIT_TRANSFER_ACCOUNT_FAILURE";

export const SET_SELECTED = "SET_SELECTED";
export const RESET_SELECTED = "RESET_SELECTED";

const byId = (state = {}, action) => {
  switch (action.type) {
      case UPDATE_TRANSFER_ACCOUNTS:
        if (action.reload) {
          return action.transfer_accounts;
        }
        return DEEEEEEP(state, action.transfer_accounts);

      case UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS:
        var newState = {};

        action.credit_transfer_list.map(transfer => {
          if (transfer.transfer_type === 'DISBURSEMENT') {
            let updatedTransferAccount = {[transfer.recipient_transfer_account.id]: {credit_receives: [transfer.id]}};
            newState = {...newState, ...updatedTransferAccount};

          } else if (transfer.transfer_type === 'RECLAMATION') {
            let updatedTransferAccount = {[transfer.sender_transfer_account.id]: {credit_sends: [transfer.id]}};
            newState = {...newState, ...updatedTransferAccount};

          }
        });

        return addCreditTransferIdsToTransferAccount(state, newState);

    default:
      return state;
  }
};

const initialPagination = {
  items: null,
  pages: 0,
};

const paginate = (state = initialPagination, action) => {
  switch (action.type) {
    case UPDATE_TRANSFER_ACCOUNT_LIST_PAGINATION:
      return {...state, items: action.items, pages: action.pages};
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
    case LOAD_TRANSFER_ACCOUNTS_REQUEST:
      return {...state, isRequesting: true};

    case LOAD_TRANSFER_ACCOUNTS_SUCCESS:
      return {...state, isRequesting: false, success: true};

    case LOAD_TRANSFER_ACCOUNTS_FAILURE:
      return {...state, isRequesting: false, error: action.error};

    default:
      return state;
  }
};

const initialEditStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const editStatus = (state = initialEditStatusState, action) => {
  switch (action.type) {
    case EDIT_TRANSFER_ACCOUNT_REQUEST:
      return {...state, isRequesting: true};

    case EDIT_TRANSFER_ACCOUNT_SUCCESS:
      return {...state, isRequesting: false, success: true};

    case EDIT_TRANSFER_ACCOUNT_FAILURE:
      return {...state, isRequesting: false, error: action.error};

    default:
      return state;
  }
};

const initialSelectedState = [];

const selected = (state = initialSelectedState, action) => {
  switch (action.type) {
    case SET_SELECTED:
      return action.selected
    case RESET_SELECTED:
      return initialSelectedState;

    default:
      return state;
  }
}


export const transferAccounts = combineReducers({
  byId,
  loadStatus,
  editStatus,
  selected,
  paginate
});

// ACTIONS
export const loadTransferAccounts = (payload) => (
  {
    type: LOAD_TRANSFER_ACCOUNTS_REQUEST,
    payload,
  }
);

export const editTransferAccount = (payload) => (
  {
    type: EDIT_TRANSFER_ACCOUNT_REQUEST,
    payload,
  }
);

export const setSelected = (selected) => (
  {
    type: SET_SELECTED,
    selected,
  }
);