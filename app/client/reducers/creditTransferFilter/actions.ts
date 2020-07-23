import { createAction, ActionsUnion } from "../../reduxUtils";

import {
  CreditTransferFilters,
  CreditTransferFiltersActionTypes
} from "./types";
import { LoadAllowedFiltersPayload } from "../metric/types";

export const CreditTransferFiltersAction = {
  loadCreditTransferFiltersRequest: (payload: LoadAllowedFiltersPayload) =>
    createAction(
      CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_REQUEST,
      payload
    ),
  loadCreditTransferFiltersSuccess: () =>
    createAction(
      CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS
    ),
  loadCreditTransferFiltersFailure: (error: string) =>
    createAction(
      CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_FAILURE,
      error
    ),
  updateCreditTransferFilters: (filters: CreditTransferFilters) =>
    createAction(
      CreditTransferFiltersActionTypes.UPDATE_CREDIT_TRANSFER_FILTERS,
      filters
    )
};
export type CreditTransferFiltersAction = ActionsUnion<
  typeof CreditTransferFiltersAction
>;
