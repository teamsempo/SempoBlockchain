import { put, takeEvery, call, all } from "redux-saga/effects";

import { AllowedFiltersAction } from "../reducers/allowedFilters/actions";
import { AllowedFiltersActionTypes as ActionTypes } from "../reducers/allowedFilters/types";

import { loadAllowedFiltersAPI } from "../api/filterAPI";
import { handleError } from "../utils";
import { LoadAllowedFiltersPayload as Payload } from "../reducers/metric/types";
import { NamedActionWithPayload } from "../reduxUtils";

function* loadAllowedFilters(
  action: NamedActionWithPayload<
    ActionTypes.LOAD_ALLOWED_FILTERS_REQUEST,
    Payload
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

    yield put(AllowedFiltersAction.updateAllowedFilters(action.name, parsed));

    yield put(AllowedFiltersAction.loadAllowedFiltersSuccess(action.name));
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      AllowedFiltersAction.loadAllowedFiltersFailure(action.name, error)
    );
  }
}

function* watchLoadAllowedFilters() {
  yield takeEvery(ActionTypes.LOAD_ALLOWED_FILTERS_REQUEST, loadAllowedFilters);
}

export default function* metricSagas() {
  yield all([watchLoadAllowedFilters()]);
}
