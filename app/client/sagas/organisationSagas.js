import { put, takeEvery, call, all } from "redux-saga/effects";
import { handleError } from "../utils";

import {
  LOAD_ORGANISATION_REQUEST,
  LOAD_ORGANISATION_SUCCESS,
  LOAD_ORGANISATION_FAILURE,
  UPDATE_ORGANISATION
} from "../reducers/organisation/types";

import { loadOrganisationAPI } from "../api/organisationApi.js";
import { ADD_FLASH_MESSAGE } from "../reducers/messageReducer";

function* updateStateFromOrganisation(data) {
  if (data.organisation !== undefined) {
    yield put({ type: UPDATE_ORGANISATION, organisation: data.organisation });
  }
}

function* loadOrganisation() {
  try {
    const load_result = yield call(loadOrganisationAPI);

    yield call(updateStateFromOrganisation, load_result.data);

    yield put({ type: LOAD_ORGANISATION_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    console.log("error is:", error);

    yield put({ type: LOAD_ORGANISATION_FAILURE, error: error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchLoadOrganisation() {
  yield takeEvery(LOAD_ORGANISATION_REQUEST, loadOrganisation);
}

export default function* organisationSagas() {
  yield all([watchLoadOrganisation()]);
}
