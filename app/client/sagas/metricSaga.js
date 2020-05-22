import { put, takeEvery, call, all } from "redux-saga/effects";

import { MetricAction, LoadMetricAction } from "../reducers/metric/actions";
import { LoadMetricsActionType } from "../reducers/metric/types";

import { loadCreditTransferStatsAPI } from "../api/creditTransferAPI.js";
import { handleError } from "../utils";

function* loadMetrics({ payload }) {
  try {
    const credit_stat_load_result = yield call(
      loadCreditTransferStatsAPI,
      payload
    );
    const metrics = credit_stat_load_result.data.transfer_stats;

    yield put(MetricAction.updateMetrics(metrics));

    yield put(LoadMetricAction.loadMetricSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadMetricAction.loadMetricFailure(error));
  }
}

function* watchLoadMetrics() {
  yield takeEvery(LoadMetricsActionType.LOAD_METRICS_REQUEST, loadMetrics);
}

export default function* metricSagas() {
  yield all([watchLoadMetrics()]);
}
