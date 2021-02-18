import { all, call, put, takeEvery } from "@redux-saga/core/effects";
import { normalize } from "normalizr";
import { message } from "antd";

import { genericGetAPI, genericPostAPI, genericPutAPI } from "./api";

import {
  APILifecycleActionTypesInterface,
  ApiRequest,
  ApiRequestAction,
  CreateRequestAction,
  EndpointedRegistration,
  EndpointedRegistrationMapping,
  LoadRequestAction,
  ModifyRequestAction,
  Result
} from "./types";
import { handleError } from "../utils";
import {
  createActionTypes,
  deepUpdateObjectsActionType,
  loadActionTypes,
  modifyActionTypes,
  replaceIDListActionType
} from "./actions";

export const sagaFactory = (
  reg: EndpointedRegistration,
  registrations: EndpointedRegistrationMapping
): any => {
  function* loadRequest(action: LoadRequestAction) {
    const normalized = yield apiRequest(genericGetAPI, loadActionTypes, action);
    if (normalized) {
      yield put({
        type: replaceIDListActionType(reg.name),
        IdList: normalized.result
      });
    }
  }

  function* createRequest(action: CreateRequestAction) {
    yield apiRequest(genericPostAPI, createActionTypes, action);
  }

  function* modifyRequest(action: ModifyRequestAction) {
    yield apiRequest(genericPutAPI, modifyActionTypes, action);
  }

  function* apiRequest(
    apiHandler: (req: ApiRequest) => Result,
    actionType: APILifecycleActionTypesInterface,
    action: ApiRequestAction
  ) {
    try {
      const url = reg.endpoint;

      const result = yield call(apiHandler, { ...action.payload, url });

      let normalizedData: any;
      let id: number | undefined;

      if (result.data) {
        const singularData = reg.singularData || url;
        const pluralData = reg.pluralData || `${url}s`;

        let dataList = result.data[pluralData] || [result.data[singularData]];

        normalizedData = normalize(dataList, reg.schema);

        id = normalizedData.result.length === 1 && normalizedData.result[0];

        yield* Object.keys(registrations).map(key => {
          let r = registrations[key];
          let plural = r.pluralData || `${r.endpoint}s`;
          let objects = normalizedData.entities[plural];
          if (objects) {
            return put({ type: deepUpdateObjectsActionType(r.name), objects });
          }
        });
      }

      yield put({
        type: actionType.success(reg.name),
        id: id
      });

      return normalizedData;
    } catch (fetch_error) {
      console.log("fetch error", fetch_error);
      const error = yield call(handleError, fetch_error);

      yield put({ type: actionType.failure(reg.name), error });
      message.error(error.message);
    }
  }

  function* watchLoadRequest() {
    yield takeEvery(loadActionTypes.request(reg.name), loadRequest);
  }

  function* watchCreateRequest() {
    yield takeEvery(createActionTypes.request(reg.name), createRequest);
  }

  function* watchModifyRequest() {
    yield takeEvery(modifyActionTypes.request(reg.name), modifyRequest);
  }

  function* yieldAllSagas() {
    yield all([watchLoadRequest(), watchCreateRequest(), watchModifyRequest()]);
  }

  return yieldAllSagas;
};
