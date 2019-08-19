import { take, fork, put, takeEvery, call, all, cancelled, cancel, race} from 'redux-saga/effects'

import {
    NEW_EXPORT_REQUEST,
    NEW_EXPORT_SUCCESS,
    NEW_EXPORT_FAILURE,
} from '../reducers/exportReducer.js';

import { exportAPI } from '../api/exportAPI'

function* newExport({export_type, include_transfers, user_type, date_range, payable_period_start_date, payable_period_end_date, selected}) {
    try {
        const result = yield call(exportAPI, export_type, include_transfers, user_type, date_range, payable_period_start_date, payable_period_end_date, selected);
        if (result.status === 'success') {
          yield put({type: NEW_EXPORT_SUCCESS, result});
        } else {
          yield put({type: NEW_EXPORT_FAILURE, error: result.message})
        }
    } catch (error) {
        yield put({type: NEW_EXPORT_FAILURE, error: error.statusText})
    }
}

function* watchNewExport() {
    yield takeEvery(NEW_EXPORT_REQUEST, newExport);
}

export default function* newExportSaga() {
    yield all([
        watchNewExport()
    ])
}