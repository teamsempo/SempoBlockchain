import { take, fork, put, takeEvery, call, all, cancelled, cancel, race} from 'redux-saga/effects'
import { store } from '../app.jsx'
import { normalize } from 'normalizr'

import {
  PUSHER_CREDIT_TRANSFER,
  UPDATE_CREDIT_TRANSFER_LIST,
  UPDATE_CREDIT_TRANSFER_STATS,
  LOAD_CREDIT_TRANSFER_LIST_REQUEST,
  LOAD_CREDIT_TRANSFER_LIST_SUCCESS,
  LOAD_CREDIT_TRANSFER_LIST_FAILURE,
  MODIFY_TRANSFER_FAILURE,
  MODIFY_TRANSFER_REQUEST,
  MODIFY_TRANSFER_SUCCESS,
  CREATE_TRANSFER_REQUEST,
  CREATE_TRANSFER_SUCCESS,
  CREATE_TRANSFER_FAILURE,
} from '../reducers/creditTransferReducer.js';

import { UPDATE_TRANSFER_ACCOUNTS, UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS } from '../reducers/transferAccountReducer.js';
import { UPDATE_USER_LIST } from "../reducers/userReducer";

import { loadCreditTransferListAPI, modifyTransferAPI, newTransferAPI } from '../api/creditTransferAPI.js'
import { creditTransferSchema } from "../schemas";
import {ADD_FLASH_MESSAGE} from "../reducers/messageReducer";
import {handleError} from "../utils";


function* updateStateFromCreditTransfer(result) {
  //Schema expects a list of credit transfer objects
  if (result.data.credit_transfers) {
    var credit_transfer_list = result.data.credit_transfers
  } else {
    credit_transfer_list = [result.data.credit_transfer]
  }

  const normalizedData = normalize(credit_transfer_list, creditTransferSchema);

  const transfer_accounts = normalizedData.entities.transfer_accounts;
  if (transfer_accounts) {
    yield put({type: UPDATE_TRANSFER_ACCOUNTS, transfer_accounts});
  }

  const users = normalizedData.entities.users;
  if (users) {
    yield put({type: UPDATE_USER_LIST, users});
  }

  if (result.message === 'Transfer Successful') {
    // a single transfer was just created!
    // we need to add the newly created credit_transfer id
    // to the associated transfer_account object credit_transfer array
    yield put({type: UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS, credit_transfer_list});
    yield put({type: ADD_FLASH_MESSAGE, error: false, message: result.message});
  }

  if (result.bulk_responses) {
    yield put({type: ADD_FLASH_MESSAGE, error: result.bulk_responses[0].status !== 200, message: result.bulk_responses[0].message});
  }

  const transfer_stats = result.data.transfer_stats;
  if (transfer_stats) {
      yield put({type: UPDATE_CREDIT_TRANSFER_STATS, transfer_stats});
  }
  const credit_transfers = normalizedData.entities.credit_transfers;

  yield put({type: UPDATE_CREDIT_TRANSFER_LIST, credit_transfers});
}

function* loadCreditTransferList({ payload }) {
  try {
    const credit_load_result = yield call(loadCreditTransferListAPI, payload);

    yield call(updateStateFromCreditTransfer, credit_load_result);

    yield put({type: LOAD_CREDIT_TRANSFER_LIST_SUCCESS});

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    yield put({type: LOAD_CREDIT_TRANSFER_LIST_FAILURE, error: error});

    yield put({type: ADD_FLASH_MESSAGE, error: true, message: error.message});
  }
}

function* watchLoadCreditTransferList() {
  yield takeEvery(LOAD_CREDIT_TRANSFER_LIST_REQUEST, loadCreditTransferList);
}

function* loadPusherCreditTransfer( pusher_data ) {
  try {
    yield call(updateStateFromCreditTransfer, pusher_data);

    yield put({type: LOAD_CREDIT_TRANSFER_LIST_SUCCESS});

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    yield put({type: LOAD_CREDIT_TRANSFER_LIST_FAILURE, error: error})
  }
}

function* watchPusherCreditTransfer() {
  yield takeEvery(PUSHER_CREDIT_TRANSFER, loadPusherCreditTransfer);
}


function* modifyTransfer({ payload }) {
  try {
    const result = yield call(modifyTransferAPI, payload);

    yield call(updateStateFromCreditTransfer, result);

    yield put({type: MODIFY_TRANSFER_SUCCESS});

    yield put({type: ADD_FLASH_MESSAGE, error: false, message: result.message});

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    yield put({type: MODIFY_TRANSFER_FAILURE, error: error});

    yield put({type: ADD_FLASH_MESSAGE, error: true, message: error.message});

  }
}

function* watchModifyTransfer() {
  yield takeEvery(MODIFY_TRANSFER_REQUEST, modifyTransfer);
}

function* createTransfer({ payload }) {
  try {
    const result = yield call(newTransferAPI, payload);

    yield call(updateStateFromCreditTransfer, result);

    yield put({type: CREATE_TRANSFER_SUCCESS});

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    yield put({type: CREATE_TRANSFER_FAILURE, error: error});

    yield put({type: ADD_FLASH_MESSAGE, error: true, message: error.message});
  }
}

function* watchCreateTransfer() {
  yield takeEvery(CREATE_TRANSFER_REQUEST, createTransfer);
}


export default function* credit_transferSagas() {
  yield all([
    watchLoadCreditTransferList(),
    watchModifyTransfer(),
    watchCreateTransfer(),
    watchPusherCreditTransfer()
  ])
}