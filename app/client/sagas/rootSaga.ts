import { all } from "redux-saga/effects";

import authSagas from "./authSagas";
import spreadsheetSagas from "./spreadsheetSagas";
import credit_transferSagas from "./creditTransferSagas";
import transferAccountSagas from "./transferAccountSagas";
import newExportSaga from "./exportSaga";
import userSagas from "./userSagas";
import filterSagas from "./filterSaga";
import businessVerificationSaga from "./businessVerificationSaga";
import wyreSaga from "./wyreSaga";
import transferUsageSagas from "./transferUsageSagas";
import organisationSagas from "./organisationSagas";
import metricSaga from "./metricSaga";
import asyncSaga from "./asyncSaga";
import allowedFilterSaga from "./allowedFilterSaga";
import transferCardSagas from "./transferCardSagas";
import tokenSagas from "./tokenSaga";
import { generatedSagas } from "../reducers/rootReducer";
import bulkTransferSagas from "./bulkTransferSagas";
import masterWalletSagas from "./masterWalletSagas";

export default function* rootSaga() {
  yield all([
    authSagas(),
    spreadsheetSagas(),
    credit_transferSagas(),
    transferAccountSagas(),
    newExportSaga(),
    userSagas(),
    filterSagas(),
    businessVerificationSaga(),
    wyreSaga(),
    transferUsageSagas(),
    organisationSagas(),
    metricSaga(),
    allowedFilterSaga(),
    transferCardSagas(),
    tokenSagas(),
    bulkTransferSagas(),
    masterWalletSagas(),
    generatedSagas(),
    asyncSaga(),
  ]);
}
