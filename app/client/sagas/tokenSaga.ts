import { put, takeEvery, call, all } from "redux-saga/effects";
import { normalize } from "normalizr";
import { message } from "antd";
import { handleError } from "../utils";

import { tokenSchema } from "../schemas";

import {
  TokenListAction,
  LoadTokenAction,
  CreateTokenAction
} from "../reducers/token/actions";
import {
  LoadTokenActionTypes,
  CreateTokenActionTypes,
  TokenData,
  CreateTokenPayload
} from "../reducers/token/types";

import { loadSavedTokens, createTokenAPI } from "../api/tokenAPI";
import { ActionWithPayload } from "../reduxUtils";

function* updateStateFromToken(data: TokenData) {
  //Schema expects a list of token objects
  if (data.tokens) {
    var token_list = data.tokens;
  } else {
    token_list = [data.token];
  }

  const normalizedData = normalize(token_list, tokenSchema);

  const tokens = normalizedData.entities.tokens;

  yield put(TokenListAction.updateTokenList(tokens));
}

function* loadTokens() {
  try {
    const load_result = yield call(loadSavedTokens);

    yield call(updateStateFromToken, load_result.data);

    yield put(LoadTokenAction.loadTokenSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadTokenAction.loadTokenFailure(error.message));
  }
}

function* watchLoadTokens() {
  yield takeEvery(LoadTokenActionTypes.LOAD_TOKENS_REQUEST, loadTokens);
}

function* createToken(
  action: ActionWithPayload<
    CreateTokenActionTypes.CREATE_TOKEN_REQUEST,
    CreateTokenPayload
  >
) {
  try {
    const result = yield call(createTokenAPI, action.payload);

    yield call(updateStateFromToken, result.data);

    yield put(CreateTokenAction.createTokenSuccess());

    message.success(result.message);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(CreateTokenAction.createTokenFailure(error.message));

    message.error(error.message);
  }
}

function* watchCreateToken() {
  yield takeEvery(CreateTokenActionTypes.CREATE_TOKEN_REQUEST, createToken);
}

export default function* tokenSagas() {
  yield all([watchLoadTokens(), watchCreateToken()]);
}
