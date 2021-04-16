import { takeEvery, all } from "redux-saga/effects";
import { message } from "antd";
import { browserHistory } from "../createStore";

import { createActionTypes } from "../genericState/actions";
import { sempoObjects } from "../reducers/rootReducer";

function* navigateToTransfers() {
  message.success("Transfer Created!");
  browserHistory.push(`/transfers/`);
}

function* watchCreateSuccess() {
  yield takeEvery(
    createActionTypes.success(sempoObjects.masterWallet.name),
    navigateToTransfers
  );
}

export default function* masterWalletSagas() {
  yield all([watchCreateSuccess()]);
}
