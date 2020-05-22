import {
  LoadFilterActionTypes,
  FilterListActionTypes,
  CreateFilterActionTypes,
  CreateFilterPayload,
  Filter
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const FilterListAction = {
  updateFilterList: (filters: Filter[]) =>
    createAction(FilterListActionTypes.UPDATE_FILTER_LIST, filters)
};
export type FilterListAction = ActionsUnion<typeof FilterListAction>;

export const LoadFilterAction = {
  loadFilterRequest: () =>
    createAction(LoadFilterActionTypes.LOAD_FILTERS_REQUEST),
  loadFilterSuccess: () =>
    createAction(LoadFilterActionTypes.LOAD_FILTERS_SUCCESS),
  loadFilterFailure: (error: string) =>
    createAction(LoadFilterActionTypes.LOAD_FILTERS_FAILURE, error)
};
export type LoadFilterAction = ActionsUnion<typeof LoadFilterAction>;

export const CreateFilterAction = {
  createFilterRequest: (payload: CreateFilterPayload) =>
    createAction(CreateFilterActionTypes.CREATE_FILTER_REQUEST, payload),
  createFilterSuccess: () =>
    createAction(CreateFilterActionTypes.CREATE_FILTER_SUCCESS),
  createFilterFailure: (error: string) =>
    createAction(CreateFilterActionTypes.CREATE_FILTER_FAILURE, error),
  createFilterReset: () =>
    createAction(CreateFilterActionTypes.RESET_CREATE_FILTER)
};
export type CreateFilterAction = ActionsUnion<typeof CreateFilterAction>;
