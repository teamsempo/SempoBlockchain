import { put, takeEvery, call, all } from 'redux-saga/effects'
import { normalize } from 'normalizr';
import { handleError } from "../utils";

import { filterSchema } from '../schemas'

import {
  UPDATE_FILTER_LIST,

  LOAD_FILTERS_REQUEST,
  LOAD_FILTERS_SUCCESS,
  LOAD_FILTERS_FAILURE,

  CREATE_FILTER_REQUEST,
  CREATE_FILTER_SUCCESS,
  CREATE_FILTER_FAILURE
} from '../reducers/filterReducer.js';

import { loadFiltersAPI, createFilterAPI } from "../api/filterAPI";
import { ADD_FLASH_MESSAGE } from "../reducers/messageReducer";

function* updateStateFromFilter(data) {
  //Schema expects a list of filter objects
  if (data.filters) {
    var filter_list = data.filters
  } else {
    filter_list = [data.filter]
  }

  const normalizedData = normalize(filter_list, filterSchema);

  const filters = normalizedData.entities.filters;

  yield put({type: UPDATE_FILTER_LIST, filters});
}

// Load Filters Saga
function* loadFilters({ payload }) {
  try {
    const load_result = yield call(loadFiltersAPI, payload);

    yield call(updateStateFromFilter, load_result.data);

    const filters = normalize(load_result.data, filterSchema).entities.filters;
    yield put({type: LOAD_FILTERS_SUCCESS, filters})

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    yield put({type: LOAD_FILTERS_FAILURE, error: error.message})
  }
}

function* watchLoadFilters() {
  yield takeEvery(LOAD_FILTERS_REQUEST, loadFilters);
}


// Create filter saga
function* createFilter({ payload }) {
  try {
    const result = yield call(createFilterAPI, payload);

    yield call(updateStateFromFilter, result.data);

    yield put({type: CREATE_FILTER_SUCCESS, result});

    yield put({type: ADD_FLASH_MESSAGE, error: false, message: result.message});

  } catch (fetch_error) {

    const error = yield call(handleError, fetch_error);

    yield put({type: CREATE_FILTER_FAILURE, error: error.message});

    yield put({type: ADD_FLASH_MESSAGE, error: true, message: error.message});
  }
}

function* watchCreateFilter() {
  yield takeEvery(CREATE_FILTER_REQUEST, createFilter);
}

export default function* filterSagas() {
  yield all([
    watchLoadFilters(),
    watchCreateFilter(),
  ])
}