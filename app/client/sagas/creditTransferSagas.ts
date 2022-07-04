import { put, takeEvery, call, all, select } from "redux-saga/effects";
import { normalize } from "normalizr";
import { message } from "antd";

import {
  ModifyCreditTransferActionTypes,
  CreditTransferActionTypes,
  LoadCreditTransferActionTypes,
} from "../reducers/creditTransfer/types";

import {
  CreditTransferAction,
  LoadCreditTransferAction,
  ModifyCreditTransferAction,
} from "../reducers/creditTransfer/actions";

import {
  LoadCreditTransferListAPI,
  modifyTransferAPI,
  newTransferAPI,
} from "../api/creditTransferAPI";
import { creditTransferSchema } from "../schemas";
import { handleError } from "../utils";
import { UserListAction } from "../reducers/user/actions";
import { MetricAction } from "../reducers/metric/actions";
import { TransferAccountAction } from "../reducers/transferAccount/actions";
import { TokenListAction } from "../reducers/token/actions";
import { ReduxState } from "../reducers/rootReducer";

interface CreditLoadApiResult {
  is_create: boolean;
  data: any;
  message: string;
  bulk_responses: any[];
}

function* updateStateFromCreditTransfer(result: CreditLoadApiResult) {
  //Schema expects a list of credit transfer objects
  let credit_transfer_list = [];
  if (result.data.credit_transfers) {
    credit_transfer_list = result.data.credit_transfers;
  } else {
    credit_transfer_list.push(result.data.credit_transfer);
  }
  const normalizedData = normalize(
    credit_transfer_list.reverse(),
    creditTransferSchema
  );

  const transfer_accounts = normalizedData.entities.transfer_accounts;
  if (transfer_accounts) {
    yield put(
      TransferAccountAction.deepUpdateTransferAccounts(transfer_accounts)
    );
  }

  const tokens = normalizedData.entities.tokens;
  if (tokens) {
    yield put(TokenListAction.updateTokenList(tokens));
  }

  const users = normalizedData.entities.users;
  if (users) {
    yield put(UserListAction.deepUpdateUserList(users));
  }

  if (result.is_create) {
    // a single transfer was just created!
    // we need to add the newly created credit_transfer id
    // to the associated transfer_account object credit_transfer array
    yield put(
      TransferAccountAction.updateTransferAccountsCreditTransfers(
        credit_transfer_list
      )
    );
    const getCreditTransfers = (state: ReduxState) =>
      state.creditTransfers.byId;
    const creditTransfers = yield select(getCreditTransfers);
    const credit_transfers = normalizedData.entities.credit_transfers;
    yield put(
      LoadCreditTransferAction.updateCreditTransferListRequest({
        ...creditTransfers,
        ...credit_transfers,
      })
    );
    message.success(result.message);
    return;
  }

  if (result.bulk_responses) {
    // bulk transfers created!
    let firstResponse = result.bulk_responses[0];
    firstResponse.status !== 201
      ? message.error(firstResponse.message)
      : message.success(firstResponse.message);
  }

  const metrics = result.data.transfer_stats;
  if (metrics) {
    yield put(MetricAction.updateMetrics(metrics));
  }
  const credit_transfers = normalizedData.entities.credit_transfers;
  yield put(
    LoadCreditTransferAction.updateCreditTransferListRequest(credit_transfers)
  );
}

interface CreditTransferListAPIResult {
  type: typeof LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST;
  payload: any;
}

function* loadPusherCreditTransfer(pusher_data: any) {
  try {
    pusher_data.is_create = true;
    yield call(updateStateFromCreditTransfer, pusher_data);
    yield put(LoadCreditTransferAction.loadCreditTransferSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put(LoadCreditTransferAction.loadCreditTransferFailure(error));
  }
}

function* watchPusherCreditTransfer() {
  yield takeEvery(
    CreditTransferActionTypes.PUSHER_CREDIT_TRANSFER,
    loadPusherCreditTransfer
  );
}

function* modifyTransfer({
  payload,
}: {
  type: typeof ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST;
  payload: any;
}) {
  try {
    const result = yield call(modifyTransferAPI, payload);

    yield call(updateStateFromCreditTransfer, result);

    yield put(ModifyCreditTransferAction.modifyTransferSuccess(result));

    message.success(result.message);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(ModifyCreditTransferAction.modifyTransferFailure(error));

    message.error(error.message);
  }
}

function* watchModifyTransfer() {
  yield takeEvery(
    ModifyCreditTransferActionTypes.MODIFY_TRANSFER_REQUEST,
    modifyTransfer
  );
}

interface CreditTransferAPIResult {
  payload: any;
}

function* createTransfer({
  payload,
}: {
  type: typeof CreditTransferActionTypes.CREATE_TRANSFER_REQUEST;
  payload: any;
}) {
  try {
    const result = yield call(newTransferAPI, payload);

    yield call(updateStateFromCreditTransfer, result);

    yield put(CreditTransferAction.createTransferSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(CreditTransferAction.createTransferFailure(error));

    message.error(error.message);
  }
}

function* watchCreateTransfer() {
  yield takeEvery(
    CreditTransferActionTypes.CREATE_TRANSFER_REQUEST,
    createTransfer
  );
}

function* loadCreditTransferList({ payload }: CreditTransferListAPIResult) {
  try {
    const credit_load_result = yield call(LoadCreditTransferListAPI, payload);
    yield call(updateStateFromCreditTransfer, credit_load_result);
    yield put(LoadCreditTransferAction.loadCreditTransferSuccess());
    if (credit_load_result.items) {
      yield put(
        LoadCreditTransferAction.updateCreditTransferPagination(
          credit_load_result.items
        )
      );
    }
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put(LoadCreditTransferAction.loadCreditTransferFailure(error));

    message.error(error.message);
  }
}

function* watchLoadCreditTransferList() {
  yield takeEvery(
    LoadCreditTransferActionTypes.LOAD_CREDIT_TRANSFER_LIST_REQUEST,
    loadCreditTransferList
  );
}

export default function* credit_transferSagas() {
  yield all([
    watchLoadCreditTransferList(),
    watchModifyTransfer(),
    watchCreateTransfer(),
    watchPusherCreditTransfer(),
  ]);
}
