import { combineReducers } from "redux";

import {
  OrganisationActionTypes,
  Organisation,
  EditOrganisationActionTypes,
  LoadOrganisationActionTypes
} from "./types";

import {
  OrganisationAction,
  EditOrganisationAction,
  LoadOrganisationAction
} from "./actions";

import { DEEEEEEP } from "../../utils";

const byId = (
  state: Organisation[] = [] || {},
  action: OrganisationAction
): Organisation[] => {
  switch (action.type) {
    case OrganisationActionTypes.UPDATE_ORGANISATION_LIST:
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

const editStatus = (state = initialState, action: EditOrganisationAction) => {
  switch (action.type) {
    case EditOrganisationActionTypes.EDIT_ORGANISATION_REQUEST:
      return { ...state, isRequesting: true };

    case EditOrganisationActionTypes.EDIT_ORGANISATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case EditOrganisationActionTypes.EDIT_ORGANISATION_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

const loadStatus = (state = initialState, action: LoadOrganisationAction) => {
  switch (action.type) {
    case LoadOrganisationActionTypes.LOAD_ORGANISATION_REQUEST:
      return { ...state, isRequesting: true };

    case LoadOrganisationActionTypes.LOAD_ORGANISATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LoadOrganisationActionTypes.LOAD_ORGANISATION_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const OrganisationReducer = combineReducers({
  byId,
  loadStatus,
  editStatus
});
