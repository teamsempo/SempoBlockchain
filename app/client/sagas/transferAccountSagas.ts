import { put, takeEvery, call, all } from "redux-saga/effects";
import { normalize } from "normalizr";
import { message } from "antd";
import { handleError } from "../utils";

import { transferAccountSchema } from "../schemas";

import {
  LoadTransferAccountAction,
  TransferAccountAction,
  EditTransferAccountAction
} from "../reducers/transferAccount/actions";
import { CreditTransferAction } from "../reducers/creditTransfer/actions";
import { UserListAction } from "../reducers/user/actions";
import { TokenListAction } from "../reducers/token/actions";

import {
  LoadTransferAccountActionTypes,
  EditTransferAccountActionTypes,
  TransferAccountEditApiResult,
  TransferAccountLoadApiResult
} from "../reducers/transferAccount/types";

import {
  TransferAccountData,
  SingularTransferAccountData,
  MultipleTransferAccountData
} from "../reducers/transferAccount/types";

import {
  loadTransferAccountListAPI,
  editTransferAccountAPI
} from "../api/transferAccountAPI";

function* updateStateFromTransferAccount(data: TransferAccountData) {
  //Schema expects a list of transfer account objects
  if ((data as MultipleTransferAccountData).transfer_accounts) {
    var transfer_account_list = (data as MultipleTransferAccountData)
      .transfer_accounts;
  } else {
    transfer_account_list = [
      (data as SingularTransferAccountData).transfer_account
    ];
  }
  const normalizedData = normalize(
    transfer_account_list,
    transferAccountSchema
  );

  const tokens = normalizedData.entities.tokens;
  if (tokens) {
    yield put(TokenListAction.updateTokenList(tokens));
  }

  const users = normalizedData.entities.users;
  if (users) {
    yield put(UserListAction.deepUpdateUserList(users));
  }

  const credit_sends = normalizedData.entities.credit_sends;
  if (credit_sends) {
    yield put(
      CreditTransferAction.updateCreditTransferListRequest(credit_sends)
    );
  }

  const credit_receives = normalizedData.entities.credit_receives;
  if (credit_receives) {
    yield put(
      CreditTransferAction.updateCreditTransferListRequest(credit_receives)
    );
  }

  const transfer_accounts = normalizedData.entities.transfer_accounts;
  if (transfer_accounts) {
    yield put(
      TransferAccountAction.deepUpdateTransferAccounts(transfer_accounts)
    );
  }

  return normalizedData;
}

function* loadTransferAccounts({ payload }: TransferAccountLoadApiResult) {
  try {
    const load_result = yield call(loadTransferAccountListAPI, payload);

    const normalized = yield call(
      updateStateFromTransferAccount,
      load_result.data
    );

    //ordered ID list with full overwrite (rather than set addition) preserves search information
    const transfer_account_id_list = normalized.result;
    if (transfer_account_id_list) {
      yield put(
        TransferAccountAction.updateTransferAccountIdList(
          transfer_account_id_list
        )
      );
    }

    yield put(
      LoadTransferAccountAction.loadTransferAccountsSuccess(
        load_result.query_time
      )
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadTransferAccountAction.loadTransferAccountsFailure(error));

    message.error(error.message);
  }
}

function* watchLoadTransferAccounts() {
  yield takeEvery(
    LoadTransferAccountActionTypes.LOAD_TRANSFER_ACCOUNTS_REQUEST,
    loadTransferAccounts
  );
}

function* editTransferAccount({ payload }: TransferAccountEditApiResult) {
  try {
    const edit_response = yield call(editTransferAccountAPI, payload);

    if (edit_response.data) {
      yield call(updateStateFromTransferAccount, edit_response.data);
    }

    yield put(EditTransferAccountAction.editTransferAccountSuccess());
    message.success(edit_response.message);
  } catch (fetch_error) {
    console.log("fe is", fetch_error)
    const error = yield call(handleError, fetch_error);

    yield put(EditTransferAccountAction.editTransferAccountFailure(error));
    message.error(error.message);
  }
}

function* watchEditTransferAccount() {
  yield takeEvery(
    EditTransferAccountActionTypes.EDIT_TRANSFER_ACCOUNT_REQUEST,
    editTransferAccount
  );
}

export default function* transferAccountSagas() {
  yield all([watchLoadTransferAccounts(), watchEditTransferAccount()]);
}
