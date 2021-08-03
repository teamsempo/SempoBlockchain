import { put, takeEvery, call, all, select } from "redux-saga/effects";
import { normalize } from "normalizr";
import { message } from "antd";
import { handleError } from "../utils";

import { userSchema } from "../schemas";

import {
  loadUserAPI,
  editUserAPI,
  deleteUserAPI,
  createUserAPI,
  resetPinAPI
} from "../api/userAPI";

import { TransferAccountAction } from "../reducers/transferAccount/actions";
import { browserHistory } from "../createStore";

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
  CreateUserPayload,
  DeleteUserActionTypes,
  DeleteUserPayload,
  EditUserActionTypes,
  EditUserPayload,
  LoadUserActionTypes,
  LoadUserRequestPayload,
  ResetPinActionTypes,
  ResetPinPayload,
  UserData,
  UserByIDs
} from "../reducers/user/types";
import { ActionWithPayload } from "../reduxUtils";
import { ReduxState } from "../reducers/rootReducer";
import { TransferAccountByIDs } from "../reducers/transferAccount/types";

function* updateStateFromUser(data: UserData) {
  //Schema expects a list of complete user objects
  if (data.users) {
    var user_list = data.users;
  } else {
    user_list = [data.user];
  }

  const normalizedData = normalize(user_list, userSchema);

  const users = normalizedData.entities.users;

  yield put(UserListAction.updateUserList(users));
}

function* loadUser(
  action: ActionWithPayload<
    LoadUserActionTypes.LOAD_USER_REQUEST,
    LoadUserRequestPayload
  >
) {
  try {
    const load_result = yield call(loadUserAPI, action.payload);

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

function* editUser(
  action: ActionWithPayload<
    EditUserActionTypes.EDIT_USER_REQUEST,
    EditUserPayload
  >
) {
  try {
    const edit_response = yield call(editUserAPI, action.payload);

    console.log("updating state from user");

    yield call(updateStateFromUser, edit_response.data);

    yield put(EditUserAction.editUserSuccess());

    message.success(edit_response.message);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(EditUserAction.editUserFailure(error.message));

    message.error(error.message);
  }
}

function* watchEditUser() {
  yield takeEvery(EditUserActionTypes.EDIT_USER_REQUEST, editUser);
}

const getUserState = (state: ReduxState): UserByIDs => state.users.byId;
const getTransferAccountState = (state: ReduxState): TransferAccountByIDs =>
  state.transferAccounts.byId;

function* deleteUser(
  action: ActionWithPayload<
    DeleteUserActionTypes.DELETE_USER_REQUEST,
    DeleteUserPayload
  >
) {
  try {
    const delete_response = yield call(deleteUserAPI, action.payload);
    yield put(DeleteUserAction.deleteUserSuccess());

    let userState = yield select(getUserState);

    // delete transfer account from local state
    let transferAccountState = yield select(getTransferAccountState);
    let transferAccounts = { ...transferAccountState };
    delete transferAccounts[
      userState[action.payload.path].default_transfer_account_id
    ];

    // delete user from local state
    let users = { ...userState };
    delete users[action.payload.path];

    yield put(UserListAction.replaceUserList(users));
    yield put(TransferAccountAction.updateTransferAccounts(transferAccounts));

    message.success(delete_response.message);
    browserHistory.push("/accounts");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(DeleteUserAction.deleteUserFailure(error.message));

    message.error(error.message);
  }
}

function* watchDeleteUser() {
  yield takeEvery(DeleteUserActionTypes.DELETE_USER_REQUEST, deleteUser);
}

function* resetPin(
  action: ActionWithPayload<
    ResetPinActionTypes.RESET_PIN_REQUEST,
    ResetPinPayload
  >
) {
  try {
    const reset_response = yield call(resetPinAPI, action.payload);

    yield call(updateStateFromUser, reset_response.data);

    yield put(ResetPinAction.resetPinSuccess());

    message.success(reset_response.message);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(ResetPinAction.resetPinFailure(error.message));

    message.error(error.message);
  }
}

function* watchResetPin() {
  yield takeEvery(ResetPinActionTypes.RESET_PIN_REQUEST, resetPin);
}

function* createUser(
  action: ActionWithPayload<
    CreateUserActionTypes.CREATE_USER_REQUEST,
    CreateUserPayload
  >
) {
  try {
    const result = yield call(createUserAPI, action.payload);

    yield call(updateStateFromUser, result.data);

    yield put(CreateUserAction.createUserSuccess(result));
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(CreateUserAction.createUserFailure(error.message));
    message.error(error.message);
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
