import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";
import { WyreAction } from "../reducers/wyre/actions";

import { WyreActionTypes, WyreState } from "../reducers/wyre/types";

import {
  loadExchangeRates,
  loadWyreAccountBalance,
  createWyreTransferRequest
} from "../api/wyreAPI";
import { handleError } from "../utils";

function* updateStateFromWyreDetails(data: WyreState) {
  let payload = data;
  if (payload) {
    yield put(WyreAction.updateWyreState(payload));
  }
}

function* loadWyreExchangeRates() {
  try {
    const load_result = yield call(loadExchangeRates);

    yield call(updateStateFromWyreDetails, load_result.data);

    yield put(WyreAction.loadExchangeRatesSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(WyreAction.loadExchangeRatesFailure(error));

    message.error(error.message);
  }
}

function* watchLoadWyreExchangeRates() {
  yield takeEvery(
    WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_REQUEST,
    loadWyreExchangeRates
  );
}

interface WyreAccountRequest {
  type: typeof WyreActionTypes.LOAD_WYRE_ACCOUNT_REQUEST;
}

function* loadWyreAccount() {
  try {
    const load_result = yield call(loadWyreAccountBalance);

    yield call(updateStateFromWyreDetails, load_result.data);

    yield put(WyreAction.loadWyreAccountSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(WyreAction.loadWyreAccountFailure(error));

    message.error(error.message);
  }
}

function* watchLoadWyreAccount() {
  yield takeEvery(WyreActionTypes.LOAD_WYRE_ACCOUNT_REQUEST, loadWyreAccount);
}

interface WyreTransferResult {
  type: typeof WyreActionTypes.CREATE_WYRE_TRANSFER_REQUEST;
  payload: any;
}

function* createWyreTransfer({ payload }: WyreTransferResult) {
  try {
    const create_result = yield call(createWyreTransferRequest, payload);

    yield call(updateStateFromWyreDetails, create_result.data);

    if (create_result.data.wyre_transfer.id !== "PREVIEW") {
      message.success("Transfer Initiated! Check emails.");
    }

    yield put(WyreAction.createWyreTransferSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(WyreAction.createWyreTransferFailure(error));

    message.error(error.message);
  }
}

function* watchCreateWyreTransfer() {
  yield takeEvery(
    WyreActionTypes.CREATE_WYRE_TRANSFER_REQUEST,
    createWyreTransfer
  );
}

export default function* wyreSaga() {
  yield all([
    watchLoadWyreExchangeRates(),
    watchLoadWyreAccount(),
    watchCreateWyreTransfer()
  ]);
}
