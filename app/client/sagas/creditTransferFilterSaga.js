import { put, takeEvery, call, all } from "redux-saga/effects";

import {
  LOAD_CREDIT_TRANSFER_FILTERS_REQUEST,
  LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS,
  LOAD_CREDIT_TRANSFER_FILTERS_FAILURE,
  UPDATE_CREDIT_TRANSFER_FILTERS
} from "../reducers/creditTransferFilterReducer";

import { loadCreditTransferFiltersAPI } from "../api/creditTransferAPI.js";

function* loadCreditTransferFilters({ payload }) {
  try {
    const credit_transfer_filters_load_result = yield call(
      loadCreditTransferFiltersAPI,
      payload
    );
    const filters = credit_transfer_filters_load_result.data.filters;
    const parsed = JSON.parse(filters);
    yield put({ type: UPDATE_CREDIT_TRANSFER_FILTERS, filters: parsed });

    yield put({ type: LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS });
  } catch (fetch_error) {
    yield put({
      type: LOAD_CREDIT_TRANSFER_FILTERS_FAILURE,
      error: fetch_error
    });
  }
}

function* watchLoadCreditTransferFilters() {
  yield takeEvery(
    LOAD_CREDIT_TRANSFER_FILTERS_REQUEST,
    loadCreditTransferFilters
  );
}

export default function* metricSagas() {
  yield all([watchLoadCreditTransferFilters()]);
}
