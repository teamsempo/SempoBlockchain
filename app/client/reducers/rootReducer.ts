import { AnyAction, combineReducers, Reducer } from "redux";
import { FormStateMap, reducer as FormReducer } from "redux-form";

import {
  activate,
  adminUsers,
  register,
  requestResetEmailState,
  resetPasswordState,
  validateTFA
} from "./auth/reducers";
import { login } from "./auth/loginReducer";
import {
  datasetList,
  datasetSave,
  spreadsheetUpload
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
import { transferCard } from "./transferCard/reducers";
import { tokens } from "./token/reducers";
import { bulkTransfers } from "./bulkTransfer/reducers";
import { all } from "redux-saga/effects";
import {
  creditTransferSchema,
  transferAccountSchema,
  bulkTransferSchema
} from "../schemas";
import {
  createReducers,
  createSagas,
  Registration,
  Body
} from "../genericState";
import { RegistrationMapping } from "../genericState/types";
import {
  CreateBulkTransferBody,
  ModifyBulkTransferBody
} from "./bulkTransfer/types";

//might be because of older version of react-redux that have to force like this...
const form = <Reducer<FormStateMap, AnyAction>>FormReducer;

interface SempoObjects extends RegistrationMapping {
  bulkTransfers: NamedRegistration<
    CreateBulkTransferBody,
    ModifyBulkTransferBody
  >;
}

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
  },
  bulkTransfers: {
    name: "bulkTransfers",
    endpoint: "disbursement",
    schema: bulkTransferSchema
  }
};

let baseReducers = createReducers(sempoObjects);
let sagalist = createSagas(sempoObjects);

export function* generatedSagas() {
  yield all(sagalist);
}

const appReducer = combineReducers({
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
  form,
  transferCard,
  tokens,
  ...baseReducers
});

const rootReducer = (state: any, action: any) => {
  if (action.type === "RESET") {
    state = undefined;
  }
  return appReducer(state, action);
};

export default rootReducer;

export type ReduxState = ReturnType<typeof rootReducer>;
