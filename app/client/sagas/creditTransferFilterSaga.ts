import { put, takeEvery, call, all } from "redux-saga/effects";

import { CreditTransferFiltersAction } from "../reducers/creditTransferFilter/actions";
import { CreditTransferFiltersActionTypes } from "../reducers/creditTransferFilter/types";

import { loadAllowedFiltersAPI } from "../api/filterAPI";
import { handleError } from "../utils";
import { LoadAllowedFiltersPayload } from "../reducers/metric/types";
import { ActionWithPayload } from "../reduxUtils";

function* loadAllowedFilters(
  action: ActionWithPayload<
    CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_REQUEST,
    LoadAllowedFiltersPayload
  >
) {
  try {
    console.log("calling load allowed filters", action.payload);

    const credit_transfer_filters_load_result = yield call(
      loadAllowedFiltersAPI,
      action.payload
    );
    const filters = credit_transfer_filters_load_result.data.filters;
    const parsed = JSON.parse(filters);

    console.log("found allowed filters", parsed);

    yield put(CreditTransferFiltersAction.updateCreditTransferFilters(parsed));

    yield put(CreditTransferFiltersAction.loadCreditTransferFiltersSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      CreditTransferFiltersAction.loadCreditTransferFiltersFailure(error)
    );
  }
}

function* watchLoadCreditTransferFilters() {
  yield takeEvery(
    CreditTransferFiltersActionTypes.LOAD_CREDIT_TRANSFER_FILTERS_REQUEST,
    loadAllowedFilters
  );
}

export default function* metricSagas() {
  yield all([watchLoadCreditTransferFilters()]);
}
