import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";
import { browserHistory } from "../createStore";

import { SpreadsheetAction } from "../reducers/spreadsheet/actions";
import {
  SpreadsheetActionTypes,
  SaveDatasetAPIRequest,
  SpreadsheetUploadAPIRequest
} from "../reducers/spreadsheet/types";

import {
  uploadSpreadsheetAPI,
  saveDatasetAPI,
  loadDatasetListAPI
} from "../api/spreadsheetAPI";
import { handleError } from "../utils";

function* spreadsheetUpload({ payload }: SpreadsheetUploadAPIRequest) {
  console.log("spreadsheetUpload", payload);
  try {
    const upload_result = yield call(uploadSpreadsheetAPI, payload);
    console.log("uploadSpreadsheetSuccess", upload_result);

    yield put(SpreadsheetAction.uploadSpreadsheetSuccess(upload_result));
    //todo: this needs to be updated as account type no longer handled via URL
    // browserHistory.push('/upload?type=' + transfer_account_type)
    browserHistory.push("/upload");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(SpreadsheetAction.uploadSpreadsheetFailure(error));

    message.error(error.message);
  }
}

function* watchSpreadsheetUpload() {
  yield takeEvery(
    SpreadsheetActionTypes.SPREADSHEET_UPLOAD_REQUEST,
    spreadsheetUpload
  );
}

function* saveDataset({ payload }: SaveDatasetAPIRequest) {
  try {
    console.log("saveDataset", payload);

    const save_result = yield call(saveDatasetAPI, payload);
    yield put(SpreadsheetAction.saveDatasetSuccess(save_result));
    console.log("saveDatasetSuccess", save_result);
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
