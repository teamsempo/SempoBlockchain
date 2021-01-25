import { combineReducers } from "redux";

import { EditTransferCardActionTypes } from "./types";

import { EditTransferCardAction } from "./actions";

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

const editStatus = (state = initialState, action: EditTransferCardAction) => {
  switch (action.type) {
    case EditTransferCardActionTypes.EDIT_TRANSFER_CARD_REQUEST:
      return { ...state, isRequesting: true };

    case EditTransferCardActionTypes.EDIT_TRANSFER_CARD_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case EditTransferCardActionTypes.EDIT_TRANSFER_CARD_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const transferCard = combineReducers({
  editStatus
});
