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
import { all } from "redux-saga/effects";
import { userSchema } from "../schemas";
import {
  createReducers,
  createSagas,
  Registration,
  Body
} from "../genericState";
import { RegistrationMapping } from "../genericState/types";

//might be because of older version of react-redux that have to force like this...
const form = <Reducer<FormStateMap, AnyAction>>FormReducer;

interface CreateUserBody {
  first_name: string;
  last_name: string;
  public_serial_number: string;
  //  And so on
}

interface ModifyUserBody {
  //Defaults to the same as create body, but can be different
  first_name: string;
  last_name: string;
  some_other_thing: boolean;
  //  And so on
}

interface SempoObjects extends RegistrationMapping {
  UserExample: Registration<CreateUserBody, ModifyUserBody>;
}

export const sempoObjects: SempoObjects = {
  UserExample: {
    name: "UserExample",
    endpoint: "user",
    schema: userSchema
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
  tokens,
  form,
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
