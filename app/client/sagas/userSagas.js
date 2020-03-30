import { put, takeEvery, call, all, select } from "redux-saga/effects";
import { normalize } from "normalizr";
import { handleError } from "../utils";

import { userSchema } from "../schemas";

import {
  UPDATE_USER_LIST,
  DEEP_UPDATE_USER_LIST,
  LOAD_USER_REQUEST,
  LOAD_USER_SUCCESS,
  LOAD_USER_FAILURE,
  EDIT_USER_REQUEST,
  EDIT_USER_SUCCESS,
  EDIT_USER_FAILURE,
  DELETE_USER_REQUEST,
  DELETE_USER_SUCCESS,
  DELETE_USER_FAILURE,
  CREATE_USER_REQUEST,
  CREATE_USER_SUCCESS,
  CREATE_USER_FAILURE
} from "../reducers/userReducer.js";

import {
  loadUserAPI,
  editUserAPI,
  deleteUserAPI,
  createUserAPI,
  resetPinAPI
} from "../api/userAPI";
import { ADD_FLASH_MESSAGE } from "../reducers/messageReducer";
import {
  RESET_PIN_FAILURE,
  RESET_PIN_REQUEST,
  RESET_PIN_SUCCESS
} from "../reducers/userReducer";
import { LOAD_TRANSFER_USAGES_REQUEST } from "../reducers/transferUsage/types";
import { UPDATE_TRANSFER_ACCOUNTS } from "../reducers/transferAccountReducer";
import { browserHistory } from "../app";

function* updateStateFromUser(data) {
  //Schema expects a list of credit transfer objects
  if (data.users) {
    var user_list = data.users;
  } else {
    user_list = [data.user];
  }

  const normalizedData = normalize(user_list, userSchema);

  const users = normalizedData.entities.users;

  yield put({ type: DEEP_UPDATE_USER_LIST, users });
}

// Load User Saga
function* loadUser({ payload }) {
  try {
    const load_result = yield call(loadUserAPI, payload);

    yield call(updateStateFromUser, load_result.data);

    const users = normalize(load_result.data, userSchema).entities.users;
    yield put({ type: LOAD_USER_SUCCESS, users });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: LOAD_USER_FAILURE, error: error });
  }
}

function* watchLoadUser() {
  yield takeEvery(LOAD_USER_REQUEST, loadUser);
}

// Edit User Saga
function* editUser({ payload }) {
  try {
    const edit_response = yield call(editUserAPI, payload);

    yield call(updateStateFromUser, edit_response.data);

    yield put({ type: EDIT_USER_SUCCESS, edit_user: edit_response });

    yield put({
      type: ADD_FLASH_MESSAGE,
      error: false,
      message: edit_response.message
    });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: EDIT_USER_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchEditUser() {
  yield takeEvery(EDIT_USER_REQUEST, editUser);
}

const getUserState = state => state.users.byId;
const getTransferAccountState = state => state.transferAccounts.byId;

function* deleteUser({ payload }) {
  try {
    const delete_response = yield call(deleteUserAPI, payload);
    yield put({ type: DELETE_USER_SUCCESS, delete_response });

    let userState = yield select(getUserState);

    // delete transfer account from local state
    let transferAccountState = yield select(getTransferAccountState);
    let transferAccounts = { ...transferAccountState };
    delete transferAccounts[
      userState[payload.path].default_transfer_account_id
    ];

    // delete user from local state
    let users = { ...userState };
    delete users[payload.path];

    yield put({ type: UPDATE_USER_LIST, users });
    yield put({
      type: UPDATE_TRANSFER_ACCOUNTS,
      transfer_accounts: transferAccounts
    });

    yield put({
      type: ADD_FLASH_MESSAGE,
      error: false,
      message: delete_response.message
    });
    browserHistory.push("/accounts");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: DELETE_USER_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchDeleteUser() {
  yield takeEvery(DELETE_USER_REQUEST, deleteUser);
}

function* resetPin({ payload }) {
  try {
    const reset_response = yield call(resetPinAPI, payload);

    yield call(updateStateFromUser, reset_response.data);

    yield put({ type: RESET_PIN_SUCCESS, reset_user: reset_response });

    yield put({
      type: ADD_FLASH_MESSAGE,
      error: false,
      message: reset_response.message
    });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: RESET_PIN_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchResetPin() {
  yield takeEvery(RESET_PIN_REQUEST, resetPin);
}

function* createUser({ payload }) {
  try {
    const result = yield call(createUserAPI, payload);

    yield call(updateStateFromUser, result.data);

    yield put({ type: CREATE_USER_SUCCESS, result });

    yield put({ type: LOAD_TRANSFER_USAGES_REQUEST });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: CREATE_USER_FAILURE, error: error.message });
  }
}

function* watchCreateUser() {
  yield takeEvery(CREATE_USER_REQUEST, createUser);
}

export default function* userSagas() {
  yield all([
    watchLoadUser(),
    watchEditUser(),
    watchDeleteUser(),
    watchCreateUser(),
    watchResetPin()
  ]);
}
