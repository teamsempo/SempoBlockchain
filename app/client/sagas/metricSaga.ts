import { put, takeEvery, call, all } from "redux-saga/effects";

import { MetricAction, LoadMetricAction } from "../reducers/metric/actions";
import {
  LoadMetricsActionType,
  LoadMetricsPayload
} from "../reducers/metric/types";

import { loadCreditTransferStatsAPI } from "../api/metricsAPI";
import { handleError } from "../utils";
import { ActionWithPayload } from "../reduxUtils";

function* loadMetrics(
  action: ActionWithPayload<
    LoadMetricsActionType.LOAD_METRICS_REQUEST,
    LoadMetricsPayload
  >
) {
  try {
    const credit_stat_load_result = yield call(
      loadCreditTransferStatsAPI,
      action.payload
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
