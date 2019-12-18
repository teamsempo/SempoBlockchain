import { put, takeEvery, call, all } from 'redux-saga/effects'

import {
  QR_CODE_REQUEST,
  QR_CODE_SUCCESS,
  QR_CODE_FAILURE,
  QR_CODE_TRANSFER_REQUEST,
  QR_CODE_TRANSFER_SUCCESS,
  QR_CODE_TRANSFER_FAILURE,
} from '../reducers/qrCodeReducer.js';

import { qrCodeCheckAPI, qrCodeTransferAPI } from '../api/qrCodeApi.js'

function* checkQrCode({ qr_data, transfer_amount }) {
  try {
    const result = yield call(qrCodeCheckAPI, qr_data, transfer_amount);
    yield put({type: QR_CODE_SUCCESS, result});
  } catch (error) {
    yield put({type: QR_CODE_FAILURE, error: error.statusText})
  }
}

function* watchQrCodeCheck() {
  yield takeEvery(QR_CODE_REQUEST, checkQrCode);
}

function* transferQrCode({ qr_data, transfer_amount, pin}) {
  try {
    const transaction_result = yield call(qrCodeTransferAPI, qr_data, transfer_amount, pin);
    yield put({type: QR_CODE_TRANSFER_SUCCESS, transaction_result});
  } catch (error) {
    yield put({type: QR_CODE_TRANSFER_FAILURE, error: error.statusText})
  }
}

function* watchTransferQrCode() {
  yield takeEvery(QR_CODE_TRANSFER_REQUEST, transferQrCode);
}

export default function* qrCodeSagas() {
  yield all([
    watchQrCodeCheck(),
    watchTransferQrCode(),
  ])
}