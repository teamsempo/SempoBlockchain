import {
  take,
  fork,
  put,
  takeEvery,
  call,
  all,
  cancelled,
  cancel,
  race
} from "redux-saga/effects";
import { handleError } from "../utils";

import { ExportAction } from "../reducers/export/actions";
import { ExportActionTypes } from "../reducers/export/types";

import { exportAPI } from "../api/exportAPI";

function* newExport({ payload }) {
  try {
    const result = yield call(exportAPI, payload);

    yield put(ExportAction.exportSuccess(result.data));
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(ExportAction.exportFailure(error.message));
  }
}

function* watchNewExport() {
  yield takeEvery(ExportActionTypes.NEW_EXPORT_REQUEST, newExport);
}

export default function* newExportSaga() {
  yield all([watchNewExport()]);
}
