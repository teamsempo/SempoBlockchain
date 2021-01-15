import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";
import { handleError } from "../utils";

import {
  LoadTransferUsageData,
  LoadTransferUsagePayload,
  LoadTransferUsagesActionTypes
} from "../reducers/transferUsage/types";

import { loadTransferUsagesAPI } from "../api/transferUsagesAPI";
import {
  LoadTransferUsagesAction,
  TransferUsageAction
} from "../reducers/transferUsage/actions";
import { ActionWithPayload } from "../reduxUtils";

function* updateStateFromTransferUsage(data: LoadTransferUsageData) {
  if (data.transfer_usages !== undefined) {
    yield put(TransferUsageAction.updateTransferUsages(data.transfer_usages));
  }
}

function* loadTransferUsages(
  action: ActionWithPayload<
    LoadTransferUsagesActionTypes.LOAD_TRANSFER_USAGES_REQUEST,
    LoadTransferUsagePayload
  >
) {
  try {
    //todo: fix this type error - optional query param
    //@ts-ignore
    const load_result = yield call(loadTransferUsagesAPI, action.payload);

    yield call(updateStateFromTransferUsage, load_result.data);

    yield put(LoadTransferUsagesAction.loadTransferUsagesSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      LoadTransferUsagesAction.loadTransferUsagesFailure(error.message)
    );

    message.error(error.message);
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
