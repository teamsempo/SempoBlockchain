import { put, takeEvery, call, all } from "redux-saga/effects";
import { browserHistory } from "../createStore.js";

import { SpreadsheetAction } from "../reducers/spreadsheet/actions";
import { SpreadsheetActionTypes } from "../reducers/spreadsheet/types";

import {
  uploadSpreadsheetAPI,
  saveDatasetAPI,
  loadDatasetListAPI
} from "../api/spreadsheetAPI.js";
import { handleError } from "../utils";
import { MessageAction } from "../reducers/message/actions";

interface SpreadsheetUploadAPIRequest {
  type: typeof SpreadsheetActionTypes.SPREADSHEET_UPLOAD_REQUEST;
  payload: any;
}

function* spreadsheetUpload({ payload }: SpreadsheetUploadAPIRequest) {
  try {
    const upload_result = yield call(uploadSpreadsheetAPI, payload);
    yield put(SpreadsheetAction.uploadSpreadsheetSuccess(upload_result));
    //todo: this needs to be updated as account type no longer handled via URL
    // browserHistory.push('/upload?type=' + transfer_account_type)
    browserHistory.push("/upload");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(SpreadsheetAction.uploadSpreadsheetFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchSpreadsheetUpload() {
  yield takeEvery(
    SpreadsheetActionTypes.SPREADSHEET_UPLOAD_REQUEST,
    spreadsheetUpload
  );
}

interface SaveDatasetAPIRequest {
  type: typeof SpreadsheetActionTypes.SAVE_DATASET_REQUEST;
  payload: any;
}

function* saveDataset({ payload }: SaveDatasetAPIRequest) {
  try {
    const save_result = yield call(saveDatasetAPI, payload);
    yield put(SpreadsheetAction.saveDatasetSuccess(save_result));
  } catch (error) {
    yield put(SpreadsheetAction.saveDatasetFailure(error.statusText));
  }
}

function* watchSaveDataset() {
  yield takeEvery(SpreadsheetActionTypes.SAVE_DATASET_REQUEST, saveDataset);
}

function* loadDatasetList() {
  try {
    const load_result = yield call(loadDatasetListAPI);
    yield put(SpreadsheetAction.loadDatasetListSuccess(load_result));
  } catch (error) {
    yield put(SpreadsheetAction.loadDatasetListFailure(error.statusText));
  }
}

function* watchLoadDatasetList() {
  yield takeEvery(
    SpreadsheetActionTypes.LOAD_DATASET_LIST_REQUEST,
    loadDatasetList
  );
}

export default function* spreadsheetSagas() {
  yield all([
    watchSaveDataset(),
    watchSpreadsheetUpload(),
    watchLoadDatasetList()
  ]);
}
