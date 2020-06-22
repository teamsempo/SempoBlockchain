import { put, takeEvery, call, all } from "redux-saga/effects";

import { WyreAction } from "../reducers/wyre/actions";

import { WyreActionTypes } from "../reducers/wyre/types";

import {
  loadExchangeRates,
  loadWyreAccountBalance,
  createWyreTransferRequest
} from "../api/wyreAPI";
import { handleError } from "../utils";
import { MessageAction } from "../reducers/message/actions";

function* updateStateFromWyreDetails(data) {
  let payload = data;
  if (payload) {
    yield put(WyreAction.updateWyreState(payload));
  }
}

function* loadWyreExchangeRates({ payload }) {
  try {
    const load_result = yield call(loadExchangeRates, payload);

    yield call(updateStateFromWyreDetails, load_result.data);

    yield put(WyreAction.loadExchangeRatesSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(WyreAction.loadExchangeRatesFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchLoadWyreExchangeRates() {
  yield takeEvery(
    WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_REQUEST,
    loadWyreExchangeRates
  );
}

function* loadWyreAccount({ payload }) {
  try {
    const load_result = yield call(loadWyreAccountBalance, payload);

    yield call(updateStateFromWyreDetails, load_result.data);

    yield put(WyreAction.loadWyreAccountSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(WyreAction.loadWyreAccountFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchLoadWyreAccount() {
  yield takeEvery(WyreActionTypes.LOAD_WYRE_ACCOUNT_REQUEST, loadWyreAccount);
}

function* createWyreTransfer({ payload }) {
  try {
    const create_result = yield call(createWyreTransferRequest, payload);

    yield call(updateStateFromWyreDetails, create_result.data);

    if (create_result.data.wyre_transfer.id !== "PREVIEW") {
      yield put(
        MessageAction.addMessage({
          error: false,
          message: "Transfer Initiated! Check emails."
        })
      );
    }

    yield put(WyreAction.createWyreTransferSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(WyreAction.createWyreTransferFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
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
