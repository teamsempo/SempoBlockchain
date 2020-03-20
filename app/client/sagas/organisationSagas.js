import { put, takeEvery, call, all } from 'redux-saga/effects';
import { normalize } from 'normalizr';
import { handleError } from '../utils';

import {
  LOAD_ORGANISATION_REQUEST,
  LOAD_ORGANISATION_SUCCESS,
  LOAD_ORGANISATION_FAILURE,
  UPDATE_ORGANISATION_LIST,
  EDIT_ORGANISATION_REQUEST,
  EDIT_ORGANISATION_SUCCESS,
  EDIT_ORGANISATION_FAILURE,
} from '../reducers/organisation/types';

import {
  loadOrganisationAPI,
  editOrganisationAPI,
} from '../api/organisationApi.js';
import { ADD_FLASH_MESSAGE } from '../reducers/messageReducer';
import { organisationSchema } from '../schemas';
import { browserHistory } from '../app';

function* updateStateFromOrganisation(data) {
  // Schema expects a list of organisation objects
  let organisation_list;
  if (data.organisations) {
    organisation_list = data.organisations;
  } else {
    organisation_list = [data.organisation];
  }

  const normalizedData = normalize(organisation_list, organisationSchema);
  const { organisations } = normalizedData.entities;

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

    yield put({ type: LOAD_ORGANISATION_FAILURE, error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchLoadOrganisation() {
  yield takeEvery(LOAD_ORGANISATION_REQUEST, loadOrganisation);
}

function* editOrganisation({ payload }) {
  try {
    const load_result = yield call(editOrganisationAPI, payload);

    yield call(updateStateFromOrganisation, load_result.data);

    yield put({ type: EDIT_ORGANISATION_SUCCESS });

    yield put({
      type: ADD_FLASH_MESSAGE,
      error: false,
      message: load_result.message,
    });
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({ type: EDIT_ORGANISATION_FAILURE, error });

    yield put({ type: ADD_FLASH_MESSAGE, error: true, message: error.message });
  }
}

function* watchEditOrganisation() {
  yield takeEvery(EDIT_ORGANISATION_REQUEST, editOrganisation);
}

export default function* organisationSagas() {
  yield all([watchLoadOrganisation(), watchEditOrganisation()]);
}
