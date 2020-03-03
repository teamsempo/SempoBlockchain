import { put, takeEvery, call, all } from "redux-saga/effects";
import { handleError } from "../utils";
import { normalize } from "normalizr";

import {
  LOAD_ORGANISATION_REQUEST,
  LOAD_ORGANISATION_SUCCESS,
  LOAD_ORGANISATION_FAILURE,
  UPDATE_ORGANISATION_LIST
} from "../reducers/organisation/types";

import { loadOrganisationAPI } from "../api/organisationApi.js";
import { ADD_FLASH_MESSAGE } from "../reducers/messageReducer";
import { organisationSchema } from "../schemas";

function* updateStateFromOrganisation(data) {
  //Schema expects a list of organisation objects
  let organisation_list;
  if (data.organisations) {
    organisation_list = data.organisations;
  } else {
    organisation_list = [data.organisation];
  }

  const normalizedData = normalize(organisation_list, organisationSchema);
  const organisations = normalizedData.entities.organisations;

  if (organisations) {
    yield put({ type: UPDATE_ORGANISATION_LIST, organisations });
  }
}

function* loadOrganisation() {
  try {
    const load_result = yield call(loadOrganisationAPI);

    yield call(updateStateFromOrganisation, load_result.data);

    yield put({ type: LOAD_ORGANISATION_SUCCESS });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

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
