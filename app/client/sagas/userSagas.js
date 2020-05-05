import { put, takeEvery, call, all, select } from "redux-saga/effects";
import { normalize } from "normalizr";
import { handleError } from "../utils";

import { userSchema } from "../schemas";

import {
  loadUserAPI,
  editUserAPI,
  deleteUserAPI,
  createUserAPI,
  resetPinAPI
} from "../api/userAPI";

import { UPDATE_TRANSFER_ACCOUNTS } from "../reducers/transferAccountReducer";
import { browserHistory } from "../app";
import { MessageAction } from "../reducers/message/actions";

import {
  CreateUserAction,
  DeleteUserAction,
  EditUserAction,
  LoadUserAction,
  ResetPinAction,
  UserListAction
} from "../reducers/user/actions";

import {
  CreateUserActionTypes,
  DeleteUserActionTypes,
  EditUserActionTypes,
  LoadUserActionTypes,
  ResetPinActionTypes
} from "../reducers/user/types";

function* updateStateFromUser(data) {
  //Schema expects a list of credit transfer objects
  if (data.users) {
    var user_list = data.users;
  } else {
    user_list = [data.user];
  }

  const normalizedData = normalize(user_list, userSchema);

  const users = normalizedData.entities.users;

  yield put(UserListAction.deepUpdateUserList(users));
}

function* loadUser({ payload }) {
  try {
    const load_result = yield call(loadUserAPI, payload);

    yield call(updateStateFromUser, load_result.data);

    yield put(LoadUserAction.loadUserSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadUserAction.loadUserFailure(error.message));
  }
}

function* watchLoadUser() {
  yield takeEvery(LoadUserActionTypes.LOAD_USER_REQUEST, loadUser);
}

function* editUser({ payload }) {
  try {
    const edit_response = yield call(editUserAPI, payload);

    yield call(updateStateFromUser, edit_response.data);

    yield put(EditUserAction.editUserSuccess());

    yield put(
      MessageAction.addMessage({ error: false, message: edit_response.message })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(EditUserAction.editUserFailure(error.message));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchEditUser() {
  yield takeEvery(EditUserActionTypes.EDIT_USER_REQUEST, editUser);
}

const getUserState = state => state.users.byId;
const getTransferAccountState = state => state.transferAccounts.byId;

function* deleteUser({ payload }) {
  try {
    const delete_response = yield call(deleteUserAPI, payload);
    yield put(DeleteUserAction.deleteUserSuccess());

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

    yield put(UserListAction.updateUserList(users));
    yield put({
      type: UPDATE_TRANSFER_ACCOUNTS,
      transfer_accounts: transferAccounts
    });

    yield put(
      MessageAction.addMessage({
        error: false,
        message: delete_response.message
      })
    );
    browserHistory.push("/accounts");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(DeleteUserAction.deleteUserFailure(error.message));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchDeleteUser() {
  yield takeEvery(DeleteUserActionTypes.DELETE_USER_REQUEST, deleteUser);
}

function* resetPin({ payload }) {
  try {
    const reset_response = yield call(resetPinAPI, payload);

    yield call(updateStateFromUser, reset_response.data);

    yield put(ResetPinAction.resetPinSuccess());

    yield put(
      MessageAction.addMessage({
        error: false,
        message: reset_response.message
      })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(ResetPinAction.resetPinFailure(error.message));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchResetPin() {
  yield takeEvery(ResetPinActionTypes.RESET_PIN_REQUEST, resetPin);
}

function* createUser({ payload }) {
  try {
    const result = yield call(createUserAPI, payload);

    yield call(updateStateFromUser, result.data);

    yield put(CreateUserAction.createUserSuccess(result));
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(CreateUserAction.createUserFailure(error.message));
  }
}

function* watchCreateUser() {
  yield takeEvery(CreateUserActionTypes.CREATE_USER_REQUEST, createUser);
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
