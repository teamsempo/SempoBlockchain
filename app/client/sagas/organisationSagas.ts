import { put, takeEvery, call, all } from "redux-saga/effects";
import { handleError } from "../utils";
import { normalize } from "normalizr";

import {
  LoadOrganisationActionTypes,
  EditOrganisationActionTypes,
  EditOrganisationPayload,
  OrganisationData
} from "../reducers/organisation/types";

import {
  EditOrganisationAction,
  LoadOrganisationAction,
  OrganisationAction
} from "../reducers/organisation/actions";

import {
  loadOrganisationAPI,
  editOrganisationAPI
} from "../api/organisationApi";

import { organisationSchema } from "../schemas";
import { MessageAction } from "../reducers/message/actions";
import { ActionWithPayload } from "../reduxUtils";

function* updateStateFromOrganisation(data: OrganisationData) {
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
    yield put(OrganisationAction.updateOrganisationList(organisations));
  }
}

function* loadOrganisation() {
  try {
    const load_result = yield call(loadOrganisationAPI);

    yield call(updateStateFromOrganisation, load_result.data);

    yield put(LoadOrganisationAction.loadOrganisationSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadOrganisationAction.loadOrganisationFailure(error.message));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchLoadOrganisation() {
  yield takeEvery(
    LoadOrganisationActionTypes.LOAD_ORGANISATION_REQUEST,
    loadOrganisation
  );
}

function* editOrganisation(
  action: ActionWithPayload<
    EditOrganisationActionTypes.EDIT_ORGANISATION_REQUEST,
    EditOrganisationPayload
  >
) {
  try {
    const load_result = yield call(editOrganisationAPI, action.payload);

    yield call(updateStateFromOrganisation, load_result.data);

    yield put(EditOrganisationAction.editOrganisationSuccess());

    yield put(
      MessageAction.addMessage({ error: false, message: load_result.message })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(EditOrganisationAction.editOrganisationFailure(error.message));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchEditOrganisation() {
  yield takeEvery(
    EditOrganisationActionTypes.EDIT_ORGANISATION_REQUEST,
    editOrganisation
  );
}

export default function* organisationSagas() {
  yield all([watchLoadOrganisation(), watchEditOrganisation()]);
}
