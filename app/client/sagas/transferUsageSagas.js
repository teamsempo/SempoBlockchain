import { put, takeEvery, call, all } from 'redux-saga/effects'
import {handleError} from "../utils";

import {
  LOAD_TRANSFER_USAGES_REQUEST,
  LOAD_TRANSFER_USAGES_SUCCESS,
  LOAD_TRANSFER_USAGES_FAILURE,
  UPDATE_TRANSFER_USAGES,
} from '../reducers/transferUsage/types';

import { loadTransferUsagesAPI } from '../api/transferUsagesAPI.js'
import {ADD_FLASH_MESSAGE} from "../reducers/messageReducer";

function* updateStateFromTransferUsage(data) {
  if (data.transfer_usages !== undefined) {
    yield put({type: UPDATE_TRANSFER_USAGES, transferUsages: data.transfer_usages});
  }
}

// Load Transfer Account List Saga
function* loadTransferUsages() {
  try {
    const load_result = yield call(loadTransferUsagesAPI);

    yield call(updateStateFromTransferUsage, load_result.data);

    yield put({type: LOAD_TRANSFER_USAGES_SUCCESS})

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    console.log('error is:', error);

    yield put({type: LOAD_TRANSFER_USAGES_FAILURE, error: error});

    yield put({type: ADD_FLASH_MESSAGE, error: true, message: error.message});
  }
}

function* watchLoadTransferUsages() {
  yield takeEvery(LOAD_TRANSFER_USAGES_REQUEST, loadTransferUsages);
}

export default function* transferAccountSagas() {
  yield all([
    watchLoadTransferUsages(),
  ])
}
