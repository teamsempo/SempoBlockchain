import {AnyAction, combineReducers, Reducer} from 'redux';
import {FormStateMap, reducer as FormReducer} from 'redux-form'

import {
  register,
  activate,
  requestResetEmailState,
  resetPasswordState,
  adminUsers,
  validateTFA
} from './auth/reducers'
import {login} from './auth/loginReducer'
import { spreadsheetUpload, datasetSave, datasetList } from './spreadsheetReducer'
import { qrCodeCheck, qrCodeTransfer } from './qrCodeReducer'
import { newExportRequest } from "./exportReducer"
import { message } from './messageReducer'
import { creditTransfers } from './creditTransferReducer'
import { transferAccounts } from "./transferAccountReducer"
import { users } from "./userReducer"
import { filters } from "./filterReducer"
import { businessVerification } from "./businessVerificationReducer"
import { wyre } from "./wyreReducer"
import {TransferUsageReducer} from "./transferUsage/reducers";
import {OrganisationReducer} from "./organisation/reducers";

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
  qrCodeCheck,
  qrCodeTransfer,
  newExportRequest,
  message,
  transferAccounts,
  users,
  creditTransfers,
  filters,
  businessVerification,
  wyre,
  transferUsages: TransferUsageReducer,
  organisation: OrganisationReducer,
  form
});

const rootReducer = (state: any, action: any) => {
    if (action.type === 'RESET') {
        state = undefined
    }
    return appReducer(state, action)
};

export default rootReducer;
export type ReduxState = ReturnType<typeof rootReducer>