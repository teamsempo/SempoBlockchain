import { put, takeEvery, call, all } from "redux-saga/effects";
import { normalize } from "normalizr";

import {
  PUSHER_CREDIT_TRANSFER // TODO UNUSED?
} from "../reducers/creditTransfer/reducers";

import {
  LoadCreditTransferActionTypes,
  ModifyCreditTransferActionTypes,
  CreditTransferActionTypes
} from "../reducers/creditTransfer/types";

import {
  updateCreditTransferListRequest,
  loadCreditTransferListRequest,
  loadCreditTransferListSuccess,
  loadCreditTransferListFailure,
  modifyTransferRequest,
  modifyTransferSuccess,
  modifyTransferFailure,
  createTransferRequest,
  createTransferSuccess,
  createTransferFailure
} from "../reducers/creditTransfer/actions";

import {
  DEEP_UPDATE_TRANSFER_ACCOUNTS,
  UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS
} from "../reducers/transferAccountReducer.js";

import {
  loadCreditTransferListAPI,
  modifyTransferAPI,
  newTransferAPI
} from "../api/creditTransferAPI.js";
import { creditTransferSchema } from "../schemas";
import { handleError } from "../utils";
import { MessageAction } from "../reducers/message/actions";
import { UserListAction } from "../reducers/user/actions";
import { MetricAction } from "../reducers/metric/actions";

function* updateStateFromCreditTransfer(result) {
  //Schema expects a list of credit transfer objects
  let credit_transfer_list = [];
  if (result.data.credit_transfers) {
    credit_transfer_list = result.data.credit_transfers;
  } else {
    credit_transfer_list.push(result.data.credit_transfer);
  }

  const normalizedData = normalize(credit_transfer_list, creditTransferSchema);

  const transfer_accounts = normalizedData.entities.transfer_accounts;
  if (transfer_accounts) {
    yield put({ type: DEEP_UPDATE_TRANSFER_ACCOUNTS, transfer_accounts });
  }

  const users = normalizedData.entities.users;
  if (users) {
    yield put(UserListAction.deepUpdateUserList(users));
  }

  if (result.is_create === true) {
    // a single transfer was just created!
    // we need to add the newly created credit_transfer id
    // to the associated transfer_account object credit_transfer array
    yield put({
      type: UPDATE_TRANSFER_ACCOUNTS_CREDIT_TRANSFERS,
      credit_transfer_list
    });
    yield put(
      MessageAction.addMessage({ error: false, message: result.message })
    );
  }

  if (result.bulk_responses) {
    // bulk transfers created!
    yield put(
      MessageAction.addMessage({
        error: result.bulk_responses[0].status !== 201,
        message: result.bulk_responses[0].message
      })
    );
  }

  const metrics = result.data.transfer_stats;
  if (metrics) {
    yield put(MetricAction.updateMetrics(metrics));
  }
  const credit_transfers = normalizedData.entities.credit_transfers;

  if (credit_transfers) {
    yield put(updateCreditTransferListRequest(credit_transfers));
  }
}

function* loadCreditTransferList({ payload }) {
  try {
    const credit_load_result = yield call(loadCreditTransferListAPI, payload);

    yield call(updateStateFromCreditTransfer, credit_load_result);

    yield put(loadCreditTransferListSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(loadCreditTransferListFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchLoadCreditTransferList() {
  yield takeEvery(
    LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST,
    loadCreditTransferList
  );
}

function* loadPusherCreditTransfer(pusher_data) {
  try {
    yield call(updateStateFromCreditTransfer, pusher_data);

    yield put(loadCreditTransferListSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(loadCreditTransferListFailure(error));
  }
}

function* watchPusherCreditTransfer() {
  yield takeEvery(PUSHER_CREDIT_TRANSFER, loadPusherCreditTransfer);
}

function* modifyTransfer({ payload }) {
  try {
    const result = yield call(modifyTransferAPI, payload);

    yield call(updateStateFromCreditTransfer, result);

    yield put(modifyTransferSuccess());

    yield put(
      MessageAction.addMessage({ error: false, message: result.message })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(modifyTransferFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchModifyTransfer() {
  yield takeEvery(
    ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST,
    modifyTransfer
  );
}

function* createTransfer({ payload }) {
  try {
    const result = yield call(newTransferAPI, payload);

    yield call(updateStateFromCreditTransfer, result);

    yield put(createTransferSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(createTransferFailure(error));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchCreateTransfer() {
  yield takeEvery(
    CreditTransferActionTypes.CREATE_TRANSFER_REQUEST,
    createTransfer
  );
}

export default function* credit_transferSagas() {
  yield all([
    watchLoadCreditTransferList(),
    watchModifyTransfer(),
    watchCreateTransfer(),
    watchPusherCreditTransfer()
  ]);
}
