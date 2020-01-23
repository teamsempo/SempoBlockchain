import { call, fork, put, take, all, cancelled, cancel, takeEvery } from 'redux-saga/effects';
import { normalize } from 'normalizr';

import {handleError, removeSessionToken, storeSessionToken, storeTFAToken, storeOrgid, removeOrgId, removeTFAToken, parseQuery} from '../utils'
import { adminUserSchema } from '../schemas'

import {
  requestApiToken,
  refreshApiToken,
  registerAPI,
  activateAPI,
  authenticatePusher,
  requestResetEmailAPI,
  ResetPasswordAPI,
  getUserList,
  updateUserAPI,
  inviteUserAPI,
  ValidateTFAAPI
} from '../api/authApi'

import {
  REAUTH_REQUEST,
  UPDATE_ACTIVE_ORG,
  LOGIN_REQUEST,
  LOGIN_SUCCESS,
  LOGIN_PARTIAL,
  LOGIN_FAILURE,
  LOGOUT,
  REGISTER_REQUEST,
  REGISTER_SUCCESS,
  REGISTER_FAILURE,
  ACTIVATE_REQUEST,
  ACTIVATE_SUCCESS,
  ACTIVATE_FAILURE,
  REQUEST_RESET_REQUEST,
  REQUEST_RESET_SUCCESS,
  REQUEST_RESET_FAILURE,
  RESET_PASSWORD_REQUEST,
  RESET_PASSWORD_SUCCESS,
  RESET_PASSWORD_FAILURE,
  LOAD_ADMIN_USER_REQUEST,
  LOAD_ADMIN_USER_SUCCESS,
  LOAD_ADMIN_USER_FAILURE,
  UPDATE_ADMIN_USER_LIST,
  EDIT_ADMIN_USER_REQUEST,
  EDIT_ADMIN_USER_SUCCESS,
  EDIT_ADMIN_USER_FAILURE,
  INVITE_USER_REQUEST,
  INVITE_USER_SUCCESS,
  INVITE_USER_FAILURE,
  VALIDATE_TFA_REQUEST,
  VALIDATE_TFA_SUCCESS,
  VALIDATE_TFA_FAILURE
} from '../reducers/auth/types';

import {browserHistory} from "../app.jsx";
import {ADD_FLASH_MESSAGE} from "../reducers/messageReducer";

function* updateStateFromAdmin(data) {
  //Schema expects a list of admin user objects
  if (data.admins) {
    var admin_list = data.admins
  } else {
    admin_list = [data.admin]
  }

  const normalizedData = normalize(admin_list, adminUserSchema);

  const admins = normalizedData.entities.admins;

  yield put({type: UPDATE_ADMIN_USER_LIST, admins});
}

function* saveOrgId({payload}) {
  try {
    yield call(storeOrgid, payload.organisationId.toString());

    let query_params = parseQuery(window.location.search)

    // if query param and payload are matching then just reload to update navbar
    if(query_params["org"] && payload.organisationId == query_params["org"]){
      window.location.reload()
    } else {
      window.location.assign("/");
    }
    
    
  } catch (e) {
    removeOrgId()
  }
}

function* watchSaveOrgId() {
  yield takeEvery(UPDATE_ACTIVE_ORG, saveOrgId);
}
export function* logout() {
    yield call(removeSessionToken);
    yield call(removeOrgId);
}

function createLoginSuccessObject(token) {
  return {
    type: LOGIN_SUCCESS,
    token: token.auth_token,
    userId: token.user_id,
    vendorId: token.vendor_id,
    email: token.email,
    adminTier: token.admin_tier,
    usdToSatoshiRate: token.usd_to_satoshi_rate,
    intercomHash: token.web_intercom_hash,
    webApiVersion: token.web_api_version,
    organisationName: token.active_organisation_name,
    organisationId: token.active_organisation_id,
    organisationToken: token.active_organisation_token,
    organisations: token.organisations,
    requireTransferCardExists: token.require_transfer_card_exists
  }
}

function* requestToken({payload}) {
  try {
    const token_response = yield call(requestApiToken, payload);

    if (token_response.status === 'success') {
      yield put(createLoginSuccessObject(token_response));
      yield call(storeSessionToken, token_response.auth_token );
      yield call (authenticatePusher);
      return token_response

    } else if (token_response.tfa_url) {
      yield call(storeSessionToken, token_response.auth_token );
      yield put({
        type: LOGIN_PARTIAL,
        error: token_response.message,
        tfaURL: token_response.tfa_url,
        tfaFailure: true
      });

      return token_response
    } else if (token_response.tfa_failure) {
      yield call(removeTFAToken); // something failed on the TFA logic
      yield call(storeSessionToken, token_response.auth_token );
      yield put({
        type: LOGIN_PARTIAL,
        error: token_response.message,
        tfaURL: null,
        tfaFailure: true});
      return token_response
    } else {
      yield put({type: LOGIN_FAILURE, error: token_response.message})
    }

  } catch(error) {
    yield put({type: LOGIN_FAILURE, error: error.statusText})
  } finally {
    if (yield cancelled()) {
      // ... put special cancellation handling code here
    }
  }
}

function* watchLoginRequest() {
  var reauth = yield call(refreshToken);
  yield takeEvery(LOGIN_REQUEST, requestToken);
}

function* refreshToken() {
  try {
    yield put({type: REAUTH_REQUEST});
    const token_request = yield call(refreshApiToken);
    if (token_request.auth_token) {
      yield put(createLoginSuccessObject(token_request));
      yield call(storeSessionToken, token_request.auth_token );
      yield call (authenticatePusher);
    }
    return token_request
  } catch(error) {
    yield put({type: LOGOUT});
    yield call(removeSessionToken);
    return error
  } finally {
    if (yield cancelled()) {
      // ... put special cancellation handling code here
    }
  }
}

function* watchLogoutRequest() {
  const action = yield takeEvery([LOGOUT, LOGIN_FAILURE], logout);
}


// Create Account Saga
function* register({payload}) {
  try {
    const registered_account = yield call(registerAPI, payload);

    if (registered_account.status === 'success' && !registered_account.auth_token) {
      // manual sign up, need to activate email
      yield put({type: REGISTER_SUCCESS, registered_account});
      yield put({type: ADD_FLASH_MESSAGE, error: false, message: registered_account.message});
      browserHistory.push('/login')

    } else if (registered_account.auth_token && !registered_account.tfa_url) {
      // email invite, auto login as email validated
      yield put({type: REGISTER_SUCCESS, registered_account});
      yield put(createLoginSuccessObject(registered_account));
      yield call(storeSessionToken, registered_account.auth_token );
      yield call (authenticatePusher);

    } else if (registered_account.tfa_url) {
      yield call(storeSessionToken, registered_account.auth_token );
      yield put({
        type: LOGIN_PARTIAL,
        error: registered_account.message,
        tfaURL: registered_account.tfa_url,
        tfaFailure: true
      });
    } else if (registered_account.tfa_failure) {
      yield call(removeTFAToken); // something failed on the TFA logic
      yield call(storeSessionToken, registered_account.auth_token );
      yield put({
        type: LOGIN_PARTIAL,
        error: registered_account.message,
        tfaURL: null,
        tfaFailure: true});
      return registered_account
    } else {
      yield put({type: REGISTER_FAILURE, error: registered_account.message});
      yield put({type: LOGIN_FAILURE, error: registered_account.message})
    }
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put({type: REGISTER_FAILURE, error: error.message})
  }
}

function* watchRegisterRequest() {
  yield takeEvery(REGISTER_REQUEST, register);
}

function* activate({activation_token}) {
  try {
    const activated_account = yield call(activateAPI, activation_token);

    if (activated_account.auth_token && !activated_account.tfa_url) {
      yield put({type: ACTIVATE_SUCCESS, activated_account});
      yield put(createLoginSuccessObject(activated_account));
      yield call(storeSessionToken, activated_account.auth_token);
      yield call (authenticatePusher);

    } else if (activated_account.tfa_url) {
      yield call(storeSessionToken, activated_account.auth_token );
      yield put({
        type: LOGIN_PARTIAL,
        error: activated_account.message,
        tfaURL: activated_account.tfa_url,
        tfaFailure: true
      });
    } else if (activated_account.tfa_failure) {
      yield call(removeTFAToken); // something failed on the TFA logic
      yield call(storeSessionToken, registered_account.auth_token );
      yield put({
        type: LOGIN_PARTIAL,
        error: activated_account.message,
        tfaURL: null,
        tfaFailure: true});
      return activated_account
    } else {
      yield put({type: ACTIVATE_FAILURE, error: activated_account.statusText})
    }

  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put({type: ACTIVATE_FAILURE, error: error.statusText})
  }
}

function* watchActivateRequest() {
  yield takeEvery(ACTIVATE_REQUEST, activate);
}

function* resetEmailRequest({email}) {
  try {
    const resetEmailResponse = yield call(requestResetEmailAPI, email);
    yield put({type: REQUEST_RESET_SUCCESS, resetEmailResponse});
  } catch (error) {
    yield put({type: REQUEST_RESET_FAILURE, error: error.statusText})
  }
}

function* watchResetEmailRequest() {
  yield takeEvery(REQUEST_RESET_REQUEST, resetEmailRequest);
}

function* resetPassword({payload}) {
  try {
    const resetPasswordResponse = yield call(ResetPasswordAPI, payload);
    yield put({type: RESET_PASSWORD_SUCCESS, resetPasswordResponse});
    yield put({type: LOGOUT});
  } catch (error) {
    yield put({type: RESET_PASSWORD_FAILURE, error: error.statusText})
  }
}

function* watchResetPassword() {
  yield takeEvery(RESET_PASSWORD_REQUEST, resetPassword);
}

function* userList() {
  try {
    const load_result = yield call(getUserList);

    yield call(updateStateFromAdmin, load_result);

    yield put({type: LOAD_ADMIN_USER_SUCCESS, load_result});

  } catch (error) {
    yield put({type: LOAD_ADMIN_USER_FAILURE, error: error.statusText})
  }
}

function* watchLoadUserList() {
  yield takeEvery(LOAD_ADMIN_USER_REQUEST, userList);
}

function* updateUserRequest({payload}) {
    try {
      const result = yield call(updateUserAPI, payload);

      yield call(updateStateFromAdmin, result.data);

      yield put({type: EDIT_ADMIN_USER_SUCCESS, result});

    } catch (error) {
        yield put({type: EDIT_ADMIN_USER_FAILURE, error: error})
    }
}

function* watchUpdateUserRequest() {
    yield takeEvery(EDIT_ADMIN_USER_REQUEST, updateUserRequest);
}

function* inviteUserRequest({ payload }) {
    try {
      const result = yield call(inviteUserAPI, payload);
      yield put({type: INVITE_USER_SUCCESS, result});
      yield put({type: ADD_FLASH_MESSAGE, error: false, message: result.message});
      browserHistory.push('/settings')
    } catch (fetch_error) {
      const error = yield call(handleError, fetch_error);
      yield put({type: INVITE_USER_FAILURE, error: error.message})
    }
}

function* watchInviteUserRequest() {
    yield takeEvery(INVITE_USER_REQUEST, inviteUserRequest);
}


function* validateTFA({payload}) {
  try {
    const validateTFAresponse = yield call(ValidateTFAAPI, payload);

    yield put({type: VALIDATE_TFA_SUCCESS, validateTFAresponse});
    yield call(storeTFAToken, validateTFAresponse.tfa_auth_token );
    yield put(createLoginSuccessObject(validateTFAresponse));
    yield call (authenticatePusher);

    return validateTFAresponse

  } catch (error) {

    const response = yield call(handleError, error);

    yield put({type: VALIDATE_TFA_FAILURE, error: response.message})
  }
}

function* watchValidateTFA() {
  yield takeEvery(VALIDATE_TFA_REQUEST, validateTFA);
}


export default function* authSagas() {
  yield all([
    watchSaveOrgId(),
    watchRegisterRequest(),
    watchLoginRequest(),
    watchLogoutRequest(),
    watchActivateRequest(),
    watchResetEmailRequest(),
    watchResetPassword(),
    watchLoadUserList(),
    watchUpdateUserRequest(),
    watchInviteUserRequest(),
    watchValidateTFA()
  ])
}