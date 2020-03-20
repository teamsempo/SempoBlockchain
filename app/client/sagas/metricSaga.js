import { put, takeEvery, call, all } from 'redux-saga/effects';

import {
  LOAD_METRICS_REQUEST,
  LOAD_METRICS_ERROR,
  LOAD_METRICS_SUCCESS,
  UPDATE_METRICS,
} from '../reducers/metricReducer';

import { loadCreditTransferStatsAPI } from '../api/creditTransferAPI.js';

function* loadMetrics({ payload }) {
  try {
    const credit_stat_load_result = yield call(
      loadCreditTransferStatsAPI,
      payload,
    );
    const metrics = credit_stat_load_result.data.transfer_stats;

    yield put({ type: UPDATE_METRICS, metrics });

    yield put({ type: LOAD_METRICS_SUCCESS });
  } catch (fetch_error) {
    yield put({ type: LOAD_METRICS_ERROR, error: fetch_error });
  }
}

function* watchLoadMetrics() {
  yield takeEvery(LOAD_METRICS_REQUEST, loadMetrics);
}

export default function* metricSagas() {
  yield all([watchLoadMetrics()]);
}
