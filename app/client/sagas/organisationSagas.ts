import { put, takeEvery, call, all } from "redux-saga/effects";
import { message } from "antd";
import { handleError } from "../utils";
import { normalize } from "normalizr";

import {
  CreateOrganisationActionTypes,
  CreateOrganisationPayload,
  LoadOrganisationActionTypes,
  EditOrganisationActionTypes,
  EditOrganisationPayload,
  OrganisationData
} from "../reducers/organisation/types";

import {
  CreateOrganisationAction,
  EditOrganisationAction,
  LoadOrganisationAction,
  OrganisationAction
} from "../reducers/organisation/actions";

import {
  createOrganisationAPI,
  loadOrganisationAPI,
  editOrganisationAPI
} from "../api/organisationApi";

import { organisationSchema } from "../schemas";
import { ActionWithPayload } from "../reduxUtils";
import { TokenListAction } from "../reducers/token/actions";
import { LoginAction } from "../reducers/auth/actions";

function* updateStateFromOrganisation(data: OrganisationData) {
  //Schema expects a list of organisation objects
  let organisation_list;
  if (data.organisations) {
    organisation_list = data.organisations;
  } else {
    organisation_list = [data.organisation];
  }

  const normalizedData = normalize(organisation_list, organisationSchema);

  const tokens = normalizedData.entities.tokens;
  if (tokens) {
    yield put(TokenListAction.updateTokenList(tokens));
  }

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

    message.error(error.message);
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

    message.success(load_result.message);
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(EditOrganisationAction.editOrganisationFailure(error.message));

    message.error(error.message);
  }
}

function* watchEditOrganisation() {
  yield takeEvery(
    EditOrganisationActionTypes.EDIT_ORGANISATION_REQUEST,
    editOrganisation
  );
}

function* createOrganisation(
  action: ActionWithPayload<
    CreateOrganisationActionTypes.CREATE_ORGANISATION_REQUEST,
    CreateOrganisationPayload
  >
) {
  try {
    const load_result = yield call(createOrganisationAPI, action.payload);

    yield call(updateStateFromOrganisation, load_result.data);

    yield put(CreateOrganisationAction.createOrganisationSuccess());

    message.success(load_result.message);

    yield put(
      LoginAction.updateActiveOrgRequest({
        organisationId: load_result.data.organisation.id
      })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(
      CreateOrganisationAction.createOrganisationFailure(error.message)
    );

    message.error(error.message);
  }
}

function* watchCreateOrganisation() {
  yield takeEvery(
    CreateOrganisationActionTypes.CREATE_ORGANISATION_REQUEST,
    createOrganisation
  );
}

export default function* organisationSagas() {
  yield all([
    watchLoadOrganisation(),
    watchEditOrganisation(),
    watchCreateOrganisation()
  ]);
}
