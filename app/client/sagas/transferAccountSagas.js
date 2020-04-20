import { put, takeEvery, call, all, delay } from "redux-saga/effects";
import { arrayOf, normalize } from "normalizr";
import { handleError } from "../utils";

import { transferAccountSchema } from "../schemas";

import {
  LOAD_TRANSFER_ACCOUNTS_REQUEST,
  LOAD_TRANSFER_ACCOUNTS_SUCCESS,
  LOAD_TRANSFER_ACCOUNTS_FAILURE,
  DEEP_UPDATE_TRANSFER_ACCOUNTS,
  EDIT_TRANSFER_ACCOUNT_REQUEST,
  EDIT_TRANSFER_ACCOUNT_SUCCESS,
  EDIT_TRANSFER_ACCOUNT_FAILURE
} from "../reducers/transferAccountReducer.js";

import { UPDATE_CREDIT_TRANSFER_LIST } from "../reducers/creditTransferReducer";

import {
  loadTransferAccountListAPI,
  editTransferAccountAPI
} from "../api/transferAccountAPI.js";

import { MessageAction } from "../reducers/message/actions";
import {UserListAction} from "../reducers/user/actions";

function* updateStateFromTransferAccount(data) {
  //Schema expects a list of transfer account objects
  if (data.transfer_accounts) {
    var transfer_account_list = data.transfer_accounts;
  } else {
    transfer_account_list = [data.transfer_account];
  }
  const normalizedData = normalize(
    transfer_account_list,
    transferAccountSchema
  );

  const users = normalizedData.entities.users;
  if (users) {
    yield put(UserListAction.deepUpdateUserList(users));
  }

  const credit_sends = normalizedData.entities.credit_sends;
  if (credit_sends) {
    yield put({
      type: UPDATE_CREDIT_TRANSFER_LIST,
      credit_transfers: credit_sends
    });
  }

  const credit_receives = normalizedData.entities.credit_receives;
  if (credit_receives) {
    yield put({
      type: UPDATE_CREDIT_TRANSFER_LIST,
      credit_transfers: credit_receives
    });
  }

  const transfer_accounts = normalizedData.entities.transfer_accounts;
  if (transfer_accounts) {
    yield put({ type: DEEP_UPDATE_TRANSFER_ACCOUNTS, transfer_accounts });
  }
}

// Load Transfer Account List Saga
function* loadTransferAccounts({ payload }) {
  try {
    const load_result = yield call(loadTransferAccountListAPI, payload);

    yield call(updateStateFromTransferAccount, load_result.data);

    yield put({
      type: LOAD_TRANSFER_ACCOUNTS_SUCCESS,
      lastQueried: load_result.query_time
    });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: LOAD_TRANSFER_ACCOUNTS_FAILURE, error: error });

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchLoadTransferAccounts() {
  yield takeEvery(LOAD_TRANSFER_ACCOUNTS_REQUEST, loadTransferAccounts);
}

// Edit Transfer Account Saga
function* editTransferAccount({ payload }) {
  try {
    const edit_response = yield call(editTransferAccountAPI, payload);

    yield call(updateStateFromTransferAccount, edit_response.data);

    yield put({ type: EDIT_TRANSFER_ACCOUNT_SUCCESS });

    yield put(
      MessageAction.addMessage({ error: false, message: edit_response.message })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: EDIT_TRANSFER_ACCOUNT_FAILURE, error: error });

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchEditTransferAccount() {
  yield takeEvery(EDIT_TRANSFER_ACCOUNT_REQUEST, editTransferAccount);
}

export default function* transferAccountSagas() {
  yield all([watchLoadTransferAccounts(), watchEditTransferAccount()]);
}
