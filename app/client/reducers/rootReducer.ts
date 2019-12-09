import { combineReducers } from 'redux';
import { reducer as FormReducer } from 'redux-form'

import {
  login,
  register,
  activate,
  requestResetEmailState,
  resetPasswordState,
  userList,
  updateUserRequest,
  inviteUserRequest,
  validateTFA
} from './authReducer'
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

const appReducer = combineReducers({
  login,
  register,
  activate,
  requestResetEmailState,
  resetPasswordState,
  validateTFA,
  userList,
  updateUserRequest,
  inviteUserRequest,
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
  form: FormReducer
});

const rootReducer = (state: any, action: any) => {
    if (action.type === 'RESET') {
        state = undefined
    }
    return appReducer(state, action)
};

export default rootReducer;
export type ReduxState = ReturnType<typeof rootReducer>