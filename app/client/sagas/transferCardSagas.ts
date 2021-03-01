import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";
import { handleError } from "../utils";

import {
  EditTransferCardActionTypes,
  EditTransferCardPayload
} from "../reducers/transferCard/types";

import { EditTransferCardAction } from "../reducers/transferCard/actions";

import { LoadUserAction } from "../reducers/user/actions";

import { editTransferCardAPI } from "../api/transferCardAPI";

import { ActionWithPayload } from "../reduxUtils";

function* editTransferCard(
  action: ActionWithPayload<
    EditTransferCardActionTypes.EDIT_TRANSFER_CARD_REQUEST,
    EditTransferCardPayload
  >
) {
  try {
    const load_result = yield call(editTransferCardAPI, action.payload);

    yield put(EditTransferCardAction.editTransferCardSuccess());

    yield put(LoadUserAction.loadUserRequest({ path: action.payload.userId }));

    message.success(load_result.message);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(EditTransferCardAction.editTransferCardFailure(error.message));

    message.error(error.message);
  }
}

function* watchEditTransferCard() {
  yield takeEvery(
    EditTransferCardActionTypes.EDIT_TRANSFER_CARD_REQUEST,
    editTransferCard
  );
}

export default function* transferCardSagas() {
  yield all([watchEditTransferCard()]);
}
