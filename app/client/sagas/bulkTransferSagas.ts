import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";

import { handleError } from "../utils";
import { browserHistory } from "../createStore";

import {
  CreateBulkTransferActionTypes,
  BulkTransferLoadApiResult,
  LoadBulkTransfersActionTypes
} from "../reducers/bulkTransfer/types";
import {
  CreateBulkTransferAction,
  LoadBulkTransfersAction
} from "../reducers/bulkTransfer/actions";
import {
  loadBulkTransfersAPI,
  newBulkTransferAPI
} from "../api/bulkTransferAPI";
import {
  LoadTransferAccountActionTypes,
  TransferAccountLoadApiResult
} from "../reducers/transferAccount/types";
import { createActionTypes } from "../genericState/actions";
import { sempoObjects } from "../reducers/rootReducer";

function* loadBulkTransfers({ payload }: BulkTransferLoadApiResult) {
  try {
    console.log("payload is", payload);
    const load_result = yield call(loadBulkTransfersAPI, payload);

    // const normalized = yield call(
    //   updateStateFromTransferAccount,
    //   load_result.data
    // );

    yield put(LoadBulkTransfersAction.loadBulkTransfersSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadBulkTransfersAction.loadBulkTransfersFailure(error));

    message.error(error.message);
  }
}

function* watchLoadBulkTransfers() {
  yield takeEvery(
    LoadBulkTransfersActionTypes.LOAD_BULK_TRANSFERS_REQUEST,
    loadBulkTransfers
  );
}

function* createBulkTransfer({
  payload
}: {
  type: typeof CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_REQUEST;
  payload: any;
}) {
  try {
    const result = yield call(newBulkTransferAPI, payload);

    yield put(CreateBulkTransferAction.createBulkTransferSuccess());

    browserHistory.push(`/bulk/${result.disbursement_id}`);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(CreateBulkTransferAction.createBulkTransferFailure(error));

    message.error(error.message);
  }
}

function* watchCreateBulkTransfer() {
  yield takeEvery(
    CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_REQUEST,
    createBulkTransfer
  );
}

interface SuccessAction {
  type: string;
  id: number;
}

function* navigateToBulkDetails({ id }: SuccessAction) {
  browserHistory.push(`/bulk/${id}`);
}

function* watchCreateSuccess() {
  yield takeEvery(
    createActionTypes.success(sempoObjects.bulkTransfers.name),
    navigateToBulkDetails
  );
}

export default function* bulkTransferSagas() {
  yield all([
    watchCreateBulkTransfer(),
    watchLoadBulkTransfers(),
    watchCreateSuccess()
  ]);
}
