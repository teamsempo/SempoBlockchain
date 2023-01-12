import { put, takeEvery, call, all } from "redux-saga/effects";

import { AsyncAction, LoadAsyncAction } from "../reducers/async/actions";
import { LoadAsyncActionType, LoadAsyncPayload } from "../reducers/async/types";

import { loadAsyncAPI } from "../api/asyncAPI";
import { handleError } from "../utils";
import { ActionWithPayload } from "../reduxUtils";

function* loadAsync(
  action: ActionWithPayload<
    LoadAsyncActionType.LOAD_ASYNC_REQUEST,
    LoadAsyncPayload
  >
) {
  try {
    const result = yield call(loadAsyncAPI, action.payload);

    yield put(AsyncAction.updateAsync(result));

    yield put(LoadAsyncAction.loadASyncSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put(LoadAsyncAction.loadAsyncFailure(error));
  }
}

function* watchLoadMetrics() {
  yield takeEvery(LoadAsyncActionType.LOAD_ASYNC_REQUEST, loadAsync);
}

export default function* metricSagas() {
  yield all([watchLoadMetrics()]);
}
