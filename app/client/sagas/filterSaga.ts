import { put, takeEvery, call, all } from "redux-saga/effects";
import { normalize } from "normalizr";
import { handleError } from "../utils";

import { filterSchema } from "../schemas";

import {
  FilterListAction,
  LoadFilterAction,
  CreateFilterAction
} from "../reducers/filter/actions";
import {
  LoadFilterActionTypes,
  CreateFilterActionTypes,
  FilterData,
  CreateFilterPayload
} from "../reducers/filter/types";

import { loadSavedFilters, createFilterAPI } from "../api/filterAPI";
import { MessageAction } from "../reducers/message/actions";
import { ActionWithPayload } from "../reduxUtils";

function* updateStateFromFilter(data: FilterData) {
  //Schema expects a list of filter objects
  if (data.filters) {
    var filter_list = data.filters;
  } else {
    filter_list = [data.filter];
  }

  const normalizedData = normalize(filter_list, filterSchema);

  const filters = normalizedData.entities.filters;

  yield put(FilterListAction.updateFilterList(filters));
}

function* loadFilters() {
  try {
    const load_result = yield call(loadSavedFilters);

    yield call(updateStateFromFilter, load_result.data);

    yield put(LoadFilterAction.loadFilterSuccess());
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(LoadFilterAction.loadFilterFailure(error.message));
  }
}

function* watchLoadFilters() {
  yield takeEvery(LoadFilterActionTypes.LOAD_FILTERS_REQUEST, loadFilters);
}

function* createFilter(
  action: ActionWithPayload<
    CreateFilterActionTypes.CREATE_FILTER_REQUEST,
    CreateFilterPayload
  >
) {
  try {
    const result = yield call(createFilterAPI, action.payload);

    yield call(updateStateFromFilter, result.data);

    yield put(CreateFilterAction.createFilterSuccess());

    yield put(
      MessageAction.addMessage({ error: false, message: result.message })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(CreateFilterAction.createFilterFailure(error.message));

    yield put(
      MessageAction.addMessage({ error: true, message: error.message })
    );
  }
}

function* watchCreateFilter() {
  yield takeEvery(CreateFilterActionTypes.CREATE_FILTER_REQUEST, createFilter);
}

export default function* filterSagas() {
  yield all([watchLoadFilters(), watchCreateFilter()]);
}
