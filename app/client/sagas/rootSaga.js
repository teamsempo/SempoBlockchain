import { all } from "redux-saga/effects";

import authSagas from "./authSagas";
import spreadsheetSagas from "./spreadsheetSagas";
import credit_transferSagas from "./creditTransferSagas";
import transferAccountSagas from "./transferAccountSagas";
import newExportSaga from "./exportSaga";
import userSagas from "./userSagas";
import watchOnAddFlashMessage from "./messageSaga";
import filterSagas from "./filterSaga";
import businessVerificationSaga from "./businessVerificationSaga";
import wyreSaga from "./wyreSaga";
import transferUsageSagas from "./transferUsageSagas";
import organisationSagas from "./organisationSagas";

export default function* rootSaga() {
  yield all([
    authSagas(),
    spreadsheetSagas(),
    credit_transferSagas(),
    watchOnAddFlashMessage(),
    transferAccountSagas(),
    newExportSaga(),
    userSagas(),
    filterSagas(),
    businessVerificationSaga(),
    wyreSaga(),
    transferUsageSagas(),
    organisationSagas()
  ]);
}
