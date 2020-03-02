import { put, takeEvery, call, all } from "redux-saga/effects";

import {
  EDIT_BUSINESS_VERIFICATION_REQUEST,
  EDIT_BUSINESS_VERIFICATION_SUCCESS,
  EDIT_BUSINESS_VERIFICATION_FAILURE,
  CREATE_BUSINESS_VERIFICATION_REQUEST,
  CREATE_BUSINESS_VERIFICATION_SUCCESS,
  CREATE_BUSINESS_VERIFICATION_FAILURE,
  LOAD_BUSINESS_VERIFICATION_REQUEST,
  LOAD_BUSINESS_VERIFICATION_SUCCESS,
  LOAD_BUSINESS_VERIFICATION_FAILURE,
  UPDATE_BUSINESS_VERIFICATION_STATE,
  UPDATE_ACTIVE_STEP,
  UPLOAD_DOCUMENT_REQUEST,
  UPLOAD_DOCUMENT_SUCCESS,
  UPLOAD_DOCUMENT_FAILURE,
  CREATE_BANK_ACCOUNT_REQUEST,
  CREATE_BANK_ACCOUNT_SUCCESS,
  CREATE_BANK_ACCOUNT_FAILURE,
  EDIT_BANK_ACCOUNT_REQUEST,
  EDIT_BANK_ACCOUNT_SUCCESS,
  EDIT_BANK_ACCOUNT_FAILURE
} from "../reducers/businessVerificationReducer";

import {
  editBusinessVerificationAPI,
  createBusinessVerificationAPI,
  loadBusinessVerificationAPI,
  uploadDocumentAPI,
  createBankAccountAPI,
  editBankAccountAPI
} from "../api/businessVerificationAPI";
import { ADD_FLASH_MESSAGE } from "../reducers/messageReducer";
import { handleError } from "../utils";

function* updateStateFromBusinessVerificationStep(data) {
  let kyc_application = data.kyc_application;
  if (kyc_application) {
    yield put({ type: UPDATE_BUSINESS_VERIFICATION_STATE, kyc_application });
  }
}

// edit business verification state Saga
function* editBusinessVerification({ payload }) {
  try {
    const edit_result = yield call(editBusinessVerificationAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, edit_result.data);

    yield put({ type: EDIT_BUSINESS_VERIFICATION_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: EDIT_BUSINESS_VERIFICATION_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchEditBusinessVerification() {
  yield takeEvery(EDIT_BUSINESS_VERIFICATION_REQUEST, editBusinessVerification);
}

// Load Transfer Account List Saga
function* loadBusinessVerification({ payload }) {
  try {
    const load_result = yield call(loadBusinessVerificationAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, load_result.data);

    if (load_result.data.kyc_application.kyc_status === "PENDING") {
      yield put({ type: UPDATE_ACTIVE_STEP, activeStep: 5 });
    }

    if (load_result.data.kyc_application.kyc_status === "INCOMPLETE") {
      yield put({ type: UPDATE_ACTIVE_STEP, activeStep: 0 });
    }

    yield put({ type: LOAD_BUSINESS_VERIFICATION_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: LOAD_BUSINESS_VERIFICATION_FAILURE, error: error });
  }
}

function* watchLoadBusinessVerification() {
  yield takeEvery(LOAD_BUSINESS_VERIFICATION_REQUEST, loadBusinessVerification);
}

// Create Business Verification Saga
function* createBusinessVerification({ payload }) {
  try {
    const create_result = yield call(createBusinessVerificationAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, create_result.data);

    yield put({ type: UPDATE_ACTIVE_STEP, activeStep: 1 });

    yield put({ type: CREATE_BUSINESS_VERIFICATION_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: CREATE_BUSINESS_VERIFICATION_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchCreateBusinessVerification() {
  yield takeEvery(
    CREATE_BUSINESS_VERIFICATION_REQUEST,
    createBusinessVerification
  );
}

// upload document saga
function* uploadDocument({ payload }) {
  try {
    const create_result = yield call(uploadDocumentAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, create_result.data);

    yield put({ type: UPLOAD_DOCUMENT_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: UPLOAD_DOCUMENT_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchUploadDocument() {
  yield takeEvery(UPLOAD_DOCUMENT_REQUEST, uploadDocument);
}

// create bank account saga
function* createBankAccount({ payload }) {
  try {
    const create_result = yield call(createBankAccountAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, create_result.data);

    yield put({ type: CREATE_BANK_ACCOUNT_SUCCESS });

    yield put({ type: UPDATE_ACTIVE_STEP, activeStep: 4 });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: CREATE_BANK_ACCOUNT_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchCreateBankAccount() {
  yield takeEvery(CREATE_BANK_ACCOUNT_REQUEST, createBankAccount);
}

// edit bank account saga
function* editBankAccount({ payload }) {
  try {
    const edit_result = yield call(editBankAccountAPI, payload);

    yield call(updateStateFromBusinessVerificationStep, edit_result.data);

    yield put({ type: EDIT_BANK_ACCOUNT_SUCCESS });

    yield put({ type: UPDATE_ACTIVE_STEP, activeStep: 4 });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: EDIT_BANK_ACCOUNT_FAILURE });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchEditBankAccount() {
  yield takeEvery(EDIT_BANK_ACCOUNT_REQUEST, editBankAccount);
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
