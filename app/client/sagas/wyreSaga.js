import { put, takeEvery, call, all } from "redux-saga/effects";

import {
  UPDATE_WYRE_STATE,
  LOAD_WYRE_EXCHANGE_RATES_REQUEST,
  LOAD_WYRE_EXCHANGE_RATES_SUCCESS,
  LOAD_WYRE_EXCHANGE_RATES_FAILURE,
  LOAD_WYRE_ACCOUNT_REQUEST,
  LOAD_WYRE_ACCOUNT_SUCCESS,
  LOAD_WYRE_ACCOUNT_FAILURE,
  CREATE_WYRE_TRANSFER_REQUEST,
  CREATE_WYRE_TRANSFER_SUCCESS,
  CREATE_WYRE_TRANSFER_FAILURE
} from "../reducers/wyreReducer";

import {
  loadExchangeRates,
  loadWyreAccountBalance,
  createWyreTransferRequest
} from "../api/wyreAPI";
import { ADD_FLASH_MESSAGE } from "../reducers/messageReducer";
import { handleError } from "../utils";

function* updateStateFromWyreDetails(data) {
  let payload = data;
  if (payload) {
    yield put({ type: UPDATE_WYRE_STATE, payload });
  }
}

function* loadWyreExchangeRates({ payload }) {
  try {
    const load_result = yield call(loadExchangeRates, payload);

    yield call(updateStateFromWyreDetails, load_result.data);

    yield put({ type: LOAD_WYRE_EXCHANGE_RATES_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: LOAD_WYRE_EXCHANGE_RATES_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchLoadWyreExchangeRates() {
  yield takeEvery(LOAD_WYRE_EXCHANGE_RATES_REQUEST, loadWyreExchangeRates);
}

function* loadWyreAccount({ payload }) {
  try {
    const load_result = yield call(loadWyreAccountBalance, payload);

    yield call(updateStateFromWyreDetails, load_result.data);

    yield put({ type: LOAD_WYRE_ACCOUNT_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: LOAD_WYRE_ACCOUNT_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchLoadWyreAccount() {
  yield takeEvery(LOAD_WYRE_ACCOUNT_REQUEST, loadWyreAccount);
}

function* createWyreTransfer({ payload }) {
  try {
    const create_result = yield call(createWyreTransferRequest, payload);

    yield call(updateStateFromWyreDetails, create_result.data);

    if (create_result.data.wyre_transfer.id !== "PREVIEW") {
      yield put({
        type: ADD_FLASH_MESSAGE,
        message: "Transfer Initiated! Check emails."
      });
    }

    yield put({ type: CREATE_WYRE_TRANSFER_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: CREATE_WYRE_TRANSFER_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchCreateWyreTransfer() {
  yield takeEvery(CREATE_WYRE_TRANSFER_REQUEST, createWyreTransfer);
}

export default function* wyreSaga() {
  yield all([
    watchLoadWyreExchangeRates(),
    watchLoadWyreAccount(),
    watchCreateWyreTransfer()
  ]);
}
