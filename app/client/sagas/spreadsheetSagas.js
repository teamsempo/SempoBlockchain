import { put, takeEvery, call, all } from "redux-saga/effects";
import { browserHistory } from "../app.jsx";

import {
  SPREADSHEET_UPLOAD_REQUEST,
  SPREADSHEET_UPLOAD_SUCCESS,
  SPREADSHEET_UPLOAD_FAILURE,
  SAVE_DATASET_REQUEST,
  SAVE_DATASET_SUCCESS,
  SAVE_DATASET_FAILURE,
  LOAD_DATASET_LIST_REQUEST,
  LOAD_DATASET_LIST_SUCCESS,
  LOAD_DATASET_LIST_FAILURE
} from "../reducers/spreadsheetReducer.js";

import {
  uploadSpreadsheetAPI,
  saveDatasetAPI,
  loadDatasetListAPI
} from "../api/spreadsheetAPI.js";
import { handleError } from "../utils";
import { MessageAction } from "../reducers/message/actions";

function* spreadsheetUpload({ payload }) {
  try {
    const upload_result = yield call(uploadSpreadsheetAPI, payload);
    yield put({ type: SPREADSHEET_UPLOAD_SUCCESS, upload_result });
    //todo: this needs to be updated as account type no longer handled via URL
    // browserHistory.push('/upload?type=' + transfer_account_type)
    browserHistory.push("/upload");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: SPREADSHEET_UPLOAD_FAILURE, error: error, preview_id });

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchSpreadsheetUpload() {
  yield takeEvery(SPREADSHEET_UPLOAD_REQUEST, spreadsheetUpload);
}

function* saveDataset({ payload }) {
  try {
    const save_result = yield call(saveDatasetAPI, payload);
    yield put({ type: SAVE_DATASET_SUCCESS, save_result });
  } catch (error) {
    yield put({ type: SAVE_DATASET_FAILURE, error: error.statusText });
  }
}

function* watchSaveDataset() {
  yield takeEvery(SAVE_DATASET_REQUEST, saveDataset);
}

function* loadDatasetList() {
  try {
    const load_result = yield call(loadDatasetListAPI);
    yield put({ type: LOAD_DATASET_LIST_SUCCESS, load_result });
  } catch (error) {
    yield put({ type: LOAD_DATASET_LIST_FAILURE, error: error.statusText });
  }
}

function* watchLoadDatasetList() {
  yield takeEvery(LOAD_DATASET_LIST_REQUEST, loadDatasetList);
}

export default function* spreadsheetSagas() {
  yield all([
    watchSaveDataset(),
    watchSpreadsheetUpload(),
    watchLoadDatasetList()
  ]);
}
