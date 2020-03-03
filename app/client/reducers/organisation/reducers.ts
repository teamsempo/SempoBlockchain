import { combineReducers } from "redux";
import {
  LOAD_ORGANISATION_REQUEST,
  UPDATE_ORGANISATION_LIST,
  LOAD_ORGANISATION_SUCCESS,
  LOAD_ORGANISATION_FAILURE,
  LoadOrganisationsAction,
  OrganisationAction,
  Organisation
} from "./types";
import { DEEEEEEP } from "../../utils";

// const data = (
//   state: Organisation | null = null,
//   action: OrganisationAction
// ): Organisation | null => {
//   switch (action.type) {
//     case UPDATE_ORGANISATION_LIST:
//       return action.organisations;
//
//     default:
//       return state;
//   }
// };

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
  loadStatus
});
