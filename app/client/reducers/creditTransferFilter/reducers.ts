import { combineReducers } from "redux";
import { DEEEEEEP } from "../../utils";

import { CreditTransferFiltersAction } from "./actions";
import { CreditTransferFiltersActionTypes } from "./types";

const creditTransferFilterState = (
  state = {},
  action: CreditTransferFiltersAction
) => {
  switch (action.type) {
    case CreditTransferFiltersActionTypes.UPDATE_CREDIT_TRANSFER_FILTERS:
      return DEEEEEEP(state, action.payload);
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
  action: CreditTransferFiltersAction
) => {
  switch (action.type) {
    case CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_REQUEST:
      return { ...state, isRequesting: true };

    case CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const creditTransferFilters = combineReducers({
  creditTransferFilterState,
  loadStatus
});
