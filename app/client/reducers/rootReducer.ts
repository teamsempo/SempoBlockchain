import { AnyAction, combineReducers, Reducer } from "redux";
import { FormStateMap, reducer as FormReducer } from "redux-form";

import {
  register,
  activate,
  requestResetEmailState,
  resetPasswordState,
  adminUsers,
  validateTFA
} from "./auth/reducers";
import { login } from "./auth/loginReducer";
import {
  spreadsheetUpload,
  datasetSave,
  datasetList
} from "./spreadsheet/reducers";
import { ExportReducer } from "./export/reducers";
import { creditTransfers } from "./creditTransfer/reducers";
import { transferAccounts } from "./transferAccount/reducers";
import { users } from "./user/reducers";
import { filters } from "./filter/reducers";
import { businessVerification } from "./businessVerification/reducers";
import { wyre } from "./wyre/reducers";
import { TransferUsageReducer } from "./transferUsage/reducers";
import { OrganisationReducer } from "./organisation/reducers";
import { metrics } from "./metric/reducers";
import { allowedFilters } from "./allowedFilters/reducers";
import { tokens } from "./token/reducers";
import { bulkTransfers } from "./bulkTransfer/reducers";
import { CreditTransferActionTypes } from "./creditTransfer/types";
import { put, takeEvery, call, all } from "redux-saga/effects";
import { LoadCreditTransferAction } from "./creditTransfer/actions";
import { loadCreditTransferListAPI } from "../api/creditTransferAPI";
import { message } from "antd";
import { DEEEEEEP, handleError } from "../utils";
import { genericGetAPI, genericPostAPI, GetRequest } from "../api/genericAPI";
import { creditTransferSchema, transferAccountSchema } from "../schemas";
import { normalize, Schema } from "normalizr";
import { ActionTypes } from "react-select";
import { CreateUserAction } from "./user/actions";
import { ActionWithPayload } from "../reduxUtils";
import { createUserAPI } from "../api/userAPI";
import { CreateUserActionTypes, CreateUserPayload } from "./user/types";
import { Body, Method } from "../api/client/types";

//might be because of older version of react-redux that have to force like this...
const form = <Reducer<FormStateMap, AnyAction>>FormReducer;

interface registrationType {
  name: string;
  schema: Schema;
  endpoint?: string;
  singularData?: string;
  pluralData?: string;
}

interface hasEndpointRegistration extends registrationType {
  endpoint: string;
}

interface registrationsType {
  [key: string]: registrationType | hasEndpointRegistration;
}

interface RequestingState {
  isRequesting: boolean;
  success: boolean;
  error: null | string;
}

interface Result {
  [key: string]: any;
}

interface ActionGenerator {
  (name: string): string;
}

interface APILifecycleActionTypesInterface {
  stage: string;
  request: ActionGenerator;
  success: ActionGenerator;
  failure: ActionGenerator;
}

class APILifeCycleActionType implements APILifecycleActionTypesInterface {
  constructor(stage: string) {
    this.stage = stage;
  }

  stage: string;
  request = (name: string) => `${this.stage}_${name}_REQUEST`;
  success = (name: string) => `${this.stage}_${name}_REQUEST`;
  failure = (name: string) => `${this.stage}_${name}_REQUEST`;
}

const loadActionTypes = new APILifeCycleActionType("LOAD");
const createActionTypes = new APILifeCycleActionType("CREATE");
const modifyActionTypes = new APILifeCycleActionType("MODIFY");
const deleteActionTypes = new APILifeCycleActionType("DELETE");

const loadRequestActionType = (name: string) => `LOAD_${name}_REQUEST`;
const loadSuccessActionType = (name: string) => `LOAD_${name}_SUCCESS`;
const loadFailureActionType = (name: string) => `LOAD_${name}_FAILURE`;

const createRequestActionType = (name: string) => `CREATE_${name}_REQUEST`;
const createSuccessActionType = (name: string) => `CREATE_${name}_SUCCESS`;
const createFailureActionType = (name: string) => `CREATE_${name}_FAILURE`;

const loaderReducerFactory = (
  reg: registrationType
): ((state: RequestingState | undefined, action: any) => RequestingState) => {
  const initialLoaderState = {
    isRequesting: false,
    success: false,
    error: null
  };
  return (
    state: RequestingState | undefined = initialLoaderState,
    action: any
  ): RequestingState => {
    switch (action.type) {
      case loadRequestActionType(reg.name):
        return { ...state, isRequesting: true };

      case loadSuccessActionType(reg.name):
        return { ...state, isRequesting: false, success: true };

      case loadFailureActionType(reg.name):
        return {
          ...state,
          isRequesting: false,
          success: false,
          error: action.error
        };

      default:
        return state;
    }
  };
};

const deepUpdateObjectsActionType = (name: string) => `DEEP_UPDATE_${name}`;
const replaceUpdateObjectsActionType = (name: string) =>
  `REPLACE_UPDATE_${name}`;

interface byIdState {
  [key: number]: any;
}

const byIdReducerFactory = (
  reg: registrationType
): ((state: byIdState | undefined, action: any) => byIdState) => {
  return (state: byIdState | undefined = {}, action: any): byIdState => {
    switch (action.type) {
      case deepUpdateObjectsActionType(reg.name):
        return DEEEEEEP(state, action.objects);

      case replaceUpdateObjectsActionType(reg.name):
        return action.objects;

      default:
        return state;
    }
  };
};

export const actionFactory = {
  load: (reg: registrationType, path?: number, query?: {}) => ({
    type: `LOAD_${reg.name}_REQUEST`,
    path: path,
    query: query
  })
};

export interface Action<T extends string> {
  type: T;
}

export interface GetRequestAction<T extends string> extends Action<T> {
  url: string;
  payload: APIReq;
}

interface CreateRequestAction<T extends string> extends Action<T> {
  body: Body;
  payload: APIReq;
}

interface ApiRequestAction {
  type: string;
  payload: APIReq;
}

interface APIReq {
  query?: object;
  body?: Body;
  path?: number;
}

interface FullAPIReq extends APIReq {
  url: string;
}

export const sagaFactory = (
  reg: hasEndpointRegistration,
  registrations: registrationsType
): any => {
  function* loadRequest(action: GetRequestAction<string>) {
    yield apiRequest(genericGetAPI, loadActionTypes, action);
  }

  function* createRequest(action: CreateRequestAction<string>) {
    yield apiRequest(genericPostAPI, createActionTypes, action);
  }

  function* apiRequest(
    apiHandler: (req: FullAPIReq) => Result,
    actionType: APILifecycleActionTypesInterface,
    action: ApiRequestAction
  ) {
    try {
      const url = reg.endpoint;

      const result = yield call(apiHandler, { ...action.payload, url });

      const singularData = reg.singularData || url;
      const pluralData = reg.pluralData || `${url}s`;

      let dataList = result.data[pluralData] || [result.data[singularData]];

      const normalizedData = normalize(dataList, reg.schema);

      yield* Object.keys(registrations).map(key => {
        let r = registrations[key];
        let plural = r.pluralData || `${r.endpoint}s`;
        let objects = normalizedData.entities[plural];
        if (objects) {
          return put({ type: deepUpdateObjectsActionType(r.name), objects });
        }
      });

      yield put({ type: actionType.success(reg.name) });
    } catch (fetch_error) {
      const error = yield call(handleError, fetch_error);

      yield put({ type: actionType.failure(reg.name), error });
      message.error(error.message);
    }
  }

  function* watchLoadRequest() {
    yield takeEvery(loadRequestActionType(reg.name), loadRequest);
  }

  function* watchCreateRequest() {
    yield takeEvery(createRequestActionType(reg.name), createRequest);
  }

  function* yieldAllSagas() {
    yield all([watchLoadRequest(), watchCreateRequest()]);
  }

  return yieldAllSagas;
};

export const sempoObjects = {
  CT: {
    name: "CT",
    endpoint: "credit_transfer",
    schema: creditTransferSchema
  },
  TA: {
    name: "TA",
    endpoint: "transfer_account",
    schema: transferAccountSchema
  }
};

interface BaseType {
  [key: string]: any;
}
const base: BaseType = {};

const sagalist: any[] = [];

function hasEndpoint(
  reg: registrationType | hasEndpointRegistration
): reg is hasEndpointRegistration {
  return (reg as hasEndpointRegistration).endpoint !== undefined;
}

const createReducers = (registrations: registrationsType) => {
  Object.keys(registrations).map(key => {
    let reg = registrations[key];
    if (hasEndpoint(reg)) {
      base[reg.name] = combineReducers({
        loadStatus: loaderReducerFactory(reg),
        byId: byIdReducerFactory(reg)
      });
      sagalist.push(sagaFactory(reg, registrations)());
    }
  });
};

createReducers(sempoObjects);

export function* generatedSagas() {
  yield all(sagalist);
}

const appReducer = combineReducers({
  ...{
    login,
    register,
    activate,
    requestResetEmailState,
    resetPasswordState,
    validateTFA,
    adminUsers,
    spreadsheetUpload,
    datasetSave,
    datasetList,
    export: ExportReducer,
    transferAccounts,
    users,
    creditTransfers,
    metrics,
    filters,
    businessVerification,
    wyre,
    transferUsages: TransferUsageReducer,
    organisations: OrganisationReducer,
    allowedFilters,
    tokens,
    form,
    bulkTransfers
  },
  ...base
});

const rootReducer = (state: any, action: any) => {
  if (action.type === "RESET") {
    state = undefined;
  }
  return appReducer(state, action);
};

export default rootReducer;

export type ReduxState = ReturnType<typeof rootReducer>;

// }
//
//
// function* loadRequest({ path, query }: GetRequestAction<string>) {
//   try {
//     const url = reg.endpoint;
//
//     const result = yield call(genericGetAPI, {url, path, query});
//
//     yield updateFromResult(url, result);
//
//     yield put({type: loadSuccessActionType(reg.name)});
//   } catch (fetch_error) {
//     const error = yield call(handleError, fetch_error);
//
//     yield put({type: loadFailureActionType(reg.name), error});
//     message.error(error.message);
//
//   }
// }

// function* createRequest({ query, body}: CreateRequestAction<string>)
// {
//   try {
//     const url = reg.endpoint;
//
//     const result = yield call(genericPostAPI,{url, query, body});
//
//     yield updateFromResult(url, result);
//
//     yield put({type: createSuccessActionType(reg.name)});
//   } catch (fetch_error) {
//     const error = yield call(handleError, fetch_error);
//
//     yield put({type: createFailureActionType(reg.name), error});
//     message.error(error.message);
//   }
// }
