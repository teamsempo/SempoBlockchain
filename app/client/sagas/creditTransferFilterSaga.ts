import { put, takeEvery, call, all } from "redux-saga/effects";

import { CreditTransferFiltersAction } from "../reducers/creditTransferFilter/actions";
import { CreditTransferFiltersActionTypes } from "../reducers/creditTransferFilter/types";

import { loadCreditTransferFiltersAPI } from "../api/creditTransferAPI";
import { handleError } from "../utils";

function* loadCreditTransferFilters() {
  try {
    const credit_transfer_filters_load_result = yield call(
      loadCreditTransferFiltersAPI
    );
    const filters = credit_transfer_filters_load_result.data.filters;
    const parsed = JSON.parse(filters);
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
    loadCreditTransferFilters
  );
}

export default function* metricSagas() {
  yield all([watchLoadCreditTransferFilters()]);
}
