import {
  createAction,
  createNamedAction,
  ActionsUnion
} from "../../reduxUtils";

import { AllowedFilters, AllowedFiltersActionTypes } from "./types";
import { LoadAllowedFiltersPayload } from "../metric/types";

export const AllowedFiltersAction = {
  loadAllowedFiltersRequest: (
    name: string,
    payload: LoadAllowedFiltersPayload
  ) =>
    createNamedAction(
      AllowedFiltersActionTypes.LOAD_ALLOWED_FILTERS_REQUEST,
      name,
      payload
    ),
  loadAllowedFiltersSuccess: (name: string) =>
    createNamedAction(
      AllowedFiltersActionTypes.LOAD_ALLOWED_FILTERS_SUCCESS,
      name
    ),
  loadAllowedFiltersFailure: (name: string, error: string) =>
    createNamedAction(
      AllowedFiltersActionTypes.LOAD_ALLOWED_FILTERS_FAILURE,
      name,
      error
    ),
  updateAllowedFilters: (name: string, filters: AllowedFilters) =>
    createNamedAction(
      AllowedFiltersActionTypes.UPDATE_ALLOWED_FILTERS,
      name,
      filters
    )
};
export type AllowedFiltersAction = ActionsUnion<typeof AllowedFiltersAction>;
