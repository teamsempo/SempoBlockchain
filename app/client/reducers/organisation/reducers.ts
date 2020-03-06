import { combineReducers } from "redux";
import {
  LOAD_ORGANISATION_REQUEST,
  UPDATE_ORGANISATION_LIST,
  LOAD_ORGANISATION_SUCCESS,
  LOAD_ORGANISATION_FAILURE,
  LoadOrganisationsAction,
  EDIT_ORGANISATION_REQUEST,
  EDIT_ORGANISATION_SUCCESS,
  EDIT_ORGANISATION_FAILURE,
  EditOrganisationAction,
  OrganisationAction,
  Organisation
} from "./types";
import { DEEEEEEP } from "../../utils";

const byId = (
  state: Organisation[] = [] || {},
  action: OrganisationAction
): Organisation[] => {
  switch (action.type) {
    case UPDATE_ORGANISATION_LIST:
      return DEEEEEEP(state, action.organisations);
    default:
      return state;
  }
};

export interface EditOrganisationState {
  isRequesting: boolean;
  error?: string;
  success: boolean;
}

const initialEditStatusState: EditOrganisationState = {
  isRequesting: false,
  success: false
};
const editStatus = (
  state = initialEditStatusState,
  action: EditOrganisationAction
): EditOrganisationState => {
  switch (action.type) {
    case EDIT_ORGANISATION_REQUEST:
      return {...state, isRequesting: true};

    case EDIT_ORGANISATION_SUCCESS:
      return {...state, isRequesting: false, success: true};

    case EDIT_ORGANISATION_FAILURE:
      return {...state, isRequesting: false, error: action.error};

    default:
      return state;
  }
};

export interface LoadOrganisationState {
  isRequesting: boolean;
  error?: string;
  success: boolean;
}
const initialLoadStatusState: LoadOrganisationState = {
  isRequesting: false,
  success: false
};
const loadStatus = (
  state = initialLoadStatusState,
  action: LoadOrganisationsAction
): LoadOrganisationState => {
  switch (action.type) {
    case LOAD_ORGANISATION_REQUEST:
      return { ...state, isRequesting: true };

    case LOAD_ORGANISATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case LOAD_ORGANISATION_FAILURE:
      return { ...state, isRequesting: false, error: action.error };

    default:
      return state;
  }
};

export const OrganisationReducer = combineReducers({
  byId,
  loadStatus,
  editStatus,
});
