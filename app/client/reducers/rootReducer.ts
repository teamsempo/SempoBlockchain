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
import { message } from "./message/reducers";
import { creditTransfers } from "./creditTransfer/reducers";
import { transferAccounts } from "./transferAccount/reducers";
import { users } from "./user/reducers";
import { filters } from "./filter/reducers";
import { businessVerification } from "./businessVerificationReducer";
import { wyre } from "./wyreReducer";
import { TransferUsageReducer } from "./transferUsage/reducers";
import { OrganisationReducer } from "./organisation/reducers";
import { metrics } from "./metric/reducers";
import { creditTransferFilters } from "./creditTransferFilter/reducers";

//might be because of older version of react-redux that have to force like this...
const form = <Reducer<FormStateMap, AnyAction>>FormReducer;

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
  message,
  transferAccounts,
  users,
  creditTransfers,
  metrics,
  filters,
  businessVerification,
  wyre,
  transferUsages: TransferUsageReducer,
  organisations: OrganisationReducer,
  form,
  creditTransferFilters
});

const rootReducer = (state: any, action: any) => {
  if (action.type === "RESET") {
    state = undefined;
  }
  return appReducer(state, action);
};

export default rootReducer;
export type ReduxState = ReturnType<typeof rootReducer>;
