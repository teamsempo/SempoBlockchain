import { put, takeEvery, call, all } from "redux-saga/effects";
import { handleError } from "../utils";

import { LoadTransferUsagesActionTypes } from "../reducers/transferUsage/types";

import { loadTransferUsagesAPI } from "../api/transferUsagesAPI.js";
import { MessageAction } from "../reducers/message/actions";
import {
  LoadTransferUsagesAction,
  TransferUsageAction
} from "../reducers/transferUsage/actions";

function* updateStateFromTransferUsage(data) {
  if (data.transfer_usages !== undefined) {
    yield put(TransferUsageAction.updateTransferUsages(data.transfer_usages));
  }
}

// Load Transfer Account List Saga
function* loadTransferUsages({ payload }) {
  try {
    const load_result = yield call(loadTransferUsagesAPI, payload);

    yield call(updateStateFromTransferUsage, load_result.data);

    yield put(LoadTransferUsagesAction.loadTransferUsagesSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      LoadTransferUsagesAction.loadTransferUsagesFailure(error.message)
    );

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchLoadTransferUsages() {
  yield takeEvery(
    LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_REQUEST,
    loadTransferUsages
  );
}

export default function* transferAccountSagas() {
  yield all([watchLoadTransferUsages()]);
}
