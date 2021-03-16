import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";

import { BusinessVerificationAction } from "../reducers/businessVerification/actions";
import {
  BusinessVerificationActionTypes,
  CreateBankAccountSagaPayload,
  CreateBusinessProfileSagaPayload,
  EditBankAccountSagaPayload,
  EditBusinessSagaPayload,
  LoadBusinessProfileSagaPayload,
  UploadDocumentSagaPayload
} from "../reducers/businessVerification/types";

import {
  editBusinessVerificationAPI,
  createBusinessVerificationAPI,
  loadBusinessVerificationAPI,
  uploadDocumentAPI,
  createBankAccountAPI,
  editBankAccountAPI
} from "../api/businessVerificationAPI";
import { handleError } from "../utils";

function* updateStateFromBusinessVerificationStep(data: any) {
  let kyc_application = data.kyc_application;
  if (kyc_application) {
    yield put(
      BusinessVerificationAction.updateBusinessVerificationState(
        kyc_application
      )
    );
  }
}

// edit business verification state Saga
function* editBusinessVerification({ payload }: EditBusinessSagaPayload) {
  try {
    const edit_result = yield call(editBusinessVerificationAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, edit_result.data);

    yield put(BusinessVerificationAction.editBusinessVerificationSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      BusinessVerificationAction.editBusinessVerificationFailure(error)
    );

    message.error(error.message);
  }
}

function* watchEditBusinessVerification() {
  yield takeEvery(
    BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_REQUEST,
    editBusinessVerification
  );
}

// Load Transfer Account List Saga
function* loadBusinessVerification({
  payload
}: LoadBusinessProfileSagaPayload) {
  try {
    const load_result = yield call(loadBusinessVerificationAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, load_result.data);

    if (load_result.data.kyc_application.kyc_status === "PENDING") {
      yield put(BusinessVerificationAction.updateActiveStep(5));
    }

    if (load_result.data.kyc_application.kyc_status === "INCOMPLETE") {
      yield put(BusinessVerificationAction.updateActiveStep(0));
    }

    yield put(BusinessVerificationAction.loadBusinessVerificationSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      BusinessVerificationAction.loadBusinessVerificationFailure(error)
    );
  }
}

function* watchLoadBusinessVerification() {
  yield takeEvery(
    BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_REQUEST,
    loadBusinessVerification
  );
}

// Create Business Verification Saga
function* createBusinessVerification({
  payload
}: CreateBusinessProfileSagaPayload) {
  try {
    const create_result = yield call(createBusinessVerificationAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, create_result.data);

    yield put(BusinessVerificationAction.updateActiveStep(1));

    yield put(BusinessVerificationAction.createBusinessVerificationSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      BusinessVerificationAction.createBusinessVerificationFailure(error)
    );
    message.error(error.message);
  }
}

function* watchCreateBusinessVerification() {
  yield takeEvery(
    BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_REQUEST,
    createBusinessVerification
  );
}

// upload document saga
function* uploadDocument({ payload }: UploadDocumentSagaPayload) {
  try {
    const create_result = yield call(uploadDocumentAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, create_result.data);

    yield put(BusinessVerificationAction.uploadDocumentSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(BusinessVerificationAction.uploadDocumentFailure(error));
    message.error(error.message);
  }
}

function* watchUploadDocument() {
  yield takeEvery(
    BusinessVerificationActionTypes.UPLOAD_DOCUMENT_REQUEST,
    uploadDocument
  );
}

// create bank account saga
function* createBankAccount({ payload }: CreateBankAccountSagaPayload) {
  try {
    const create_result = yield call(createBankAccountAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, create_result.data);

    yield put(BusinessVerificationAction.createBankAccountSuccess());

    yield put(BusinessVerificationAction.updateActiveStep(4));
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(BusinessVerificationAction.createBankAccountFailure(error));
    message.error(error.message);
  }
}

function* watchCreateBankAccount() {
  yield takeEvery(
    BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_REQUEST,
    createBankAccount
  );
}

// edit bank account saga
function* editBankAccount({ payload }: EditBankAccountSagaPayload) {
  try {
    const edit_result = yield call(editBankAccountAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, edit_result.data);

    yield put(BusinessVerificationAction.editBankAccountSuccess());

    yield put(BusinessVerificationAction.updateActiveStep(4));
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(BusinessVerificationAction.editBankAccountFailure(error));
    message.error(error.message);
  }
}

function* watchEditBankAccount() {
  yield takeEvery(
    BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_REQUEST,
    editBankAccount
  );
}

export default function* businessVerificationSaga() {
  yield all([
    watchEditBusinessVerification(),
    watchLoadBusinessVerification(),
    watchCreateBusinessVerification(),
    watchUploadDocument(),
    watchCreateBankAccount(),
    watchEditBankAccount()
  ]);
}
