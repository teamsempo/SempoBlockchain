import {
  call,
  put,
  all,
  cancelled,
  takeEvery,
  select
} from "redux-saga/effects";
import { normalize } from "normalizr";

import {
  handleError,
  removeSessionToken,
  storeSessionToken,
  storeTFAToken,
  storeOrgid,
  removeOrgId,
  removeTFAToken,
  parseQuery
} from "../utils";
import {
  adminUserSchema,
  inviteUserSchema,
  organisationSchema
} from "../schemas";

import {
  requestApiToken,
  refreshApiToken,
  registerAPI,
  activateAPI,
  requestResetEmailAPI,
  ResetPasswordAPI,
  getUserList,
  updateUserAPI,
  inviteUserAPI,
  deleteInviteAPI,
  ValidateTFAAPI
} from "../api/authAPI";

import { authenticatePusher } from "../api/pusherAPI";

import {
  LoginActionTypes,
  RegisterActionTypes,
  ResetPasswordEmailActionTypes,
  ResetPasswordActionTypes,
  ActivateActionTypes,
  LoadAdminUserListActionTypes,
  EditAdminUserActionTypes,
  DeleteInviteActionTypes,
  InviteUserActionTypes,
  ValidateTfaActionTypes
} from "../reducers/auth/types";

import {
  AdminUserListAction,
  InviteUserListAction,
  LoginAction,
  RegisterAction,
  ActivateAccountAction,
  ResetPasswordEmailAction,
  ResetPasswordAction,
  LoadAdminUserListAction,
  EditAdminUserAction,
  DeleteInviteAction,
  InviteUserAction,
  ValidateTfaAction
} from "../reducers/auth/actions";

import { browserHistory } from "../app.jsx";
import { MessageAction } from "../reducers/message/actions";
import { OrganisationAction } from "../reducers/organisation/actions";

function* updateStateFromAdmin(data) {
  //Schema expects a list of admin user objects
  let admin_list;
  let invite_list;

  if (data.admins) {
    admin_list = data.admins;
  } else {
    admin_list = [data.admin];
  }

  if (data.invites) {
    invite_list = data.invites;
  } else {
    invite_list = [data.invite];
  }

  const normalizeAdminData = normalize(admin_list, adminUserSchema);
  const normalizeInviteData = normalize(invite_list, inviteUserSchema);

  const admins = normalizeAdminData.entities.admins;
  const invites = normalizeInviteData.entities.invites;

  yield put(AdminUserListAction.updateAdminUserList(admins));
  yield put(InviteUserListAction.deepUpdateInviteUsers(invites || []));
}

export function* updateOrganisationStateFromLoginData(data) {
  //Schema expects a list of organisation objects
  let organisation_list;
  if (data.organisations) {
    organisation_list = data.organisations;
  } else {
    organisation_list = [data.organisation];
  }

  const normalizedData = normalize(organisation_list, organisationSchema);
  const organisations = normalizedData.entities.organisations;

  if (organisations) {
    yield put(OrganisationAction.updateOrganisationList(organisations));
  }
}

function* saveOrgId({ payload }) {
  try {
    yield call(storeOrgid, payload.organisationId.toString());

    let query_params = parseQuery(window.location.search);

    // if query param and payload are matching then just reload to update navbar
    if (
      query_params["org"] &&
      payload.organisationId.toString() === query_params["org"]
    ) {
      window.location.reload();
    } else {
      window.location.assign("/");
    }
  } catch (e) {
    removeOrgId();
  }
}

function* watchSaveOrgId() {
  yield takeEvery(LoginActionTypes.UPDATE_ACTIVE_ORG, saveOrgId);
}
export function* logout() {
  yield call(removeSessionToken);
  yield call(removeOrgId);
}

function createLoginSuccessObject(token) {
  return {
    token: token.auth_token,
    userId: token.user_id,
    email: token.email,
    adminTier: token.admin_tier,
    usdToSatoshiRate: token.usd_to_satoshi_rate,
    intercomHash: token.web_intercom_hash,
    webApiVersion: token.web_api_version,
    organisationId: token.active_organisation_id
  };
}

function* requestToken({ payload }) {
  try {
    const token_response = yield call(requestApiToken, payload);

    if (token_response.status === "success") {
      yield put(
        LoginAction.loginSuccess(createLoginSuccessObject(token_response))
      );
      yield call(updateOrganisationStateFromLoginData, token_response);
      yield call(storeSessionToken, token_response.auth_token);
      yield call(authenticatePusher);
      return token_response;
    } else if (token_response.tfa_url) {
      yield call(storeSessionToken, token_response.auth_token);
      yield put(
        LoginAction.loginPartial({
          error: token_response.message,
          tfaURL: token_response.tfa_url,
          tfaFailure: true
        })
      );

      return token_response;
    } else if (token_response.tfa_failure) {
      yield call(removeTFAToken); // something failed on the TFA logic
      yield call(storeSessionToken, token_response.auth_token);
      yield put(
        LoginAction.loginPartial({
          error: token_response.message,
          tfaURL: null,
          tfaFailure: true
        })
      );
      return token_response;
    } else {
      yield put(LoginAction.loginFailure(token_response.message));
    }
  } catch (error) {
    yield put(LoginAction.loginFailure(error.statusText));
  } finally {
    if (yield cancelled()) {
      // ... put special cancellation handling code here
    }
  }
}

function* watchLoginRequest() {
  yield call(refreshToken);
  yield takeEvery(LoginActionTypes.LOGIN_REQUEST, requestToken);
}

function* refreshToken() {
  try {
    yield put(LoginAction.reauthRequest());
    const token_request = yield call(refreshApiToken);
    if (token_request.auth_token) {
      yield put(
        LoginAction.loginSuccess(createLoginSuccessObject(token_request))
      );
      yield call(updateOrganisationStateFromLoginData, token_request);
      yield call(storeSessionToken, token_request.auth_token);
      yield call(authenticatePusher);
    }
    return token_request;
  } catch (error) {
    yield put(LoginAction.logout());
    yield call(removeSessionToken);
    return error;
  } finally {
    if (yield cancelled()) {
      // ... put special cancellation handling code here
    }
  }
}

function* watchLogoutRequest() {
  yield takeEvery(
    [LoginActionTypes.LOGOUT, LoginActionTypes.LOGIN_FAILURE],
    logout
  );
}

// Create Account Saga
function* register({ payload }) {
  try {
    const registered_account = yield call(registerAPI, payload);

    if (
      registered_account.status === "success" &&
      !registered_account.auth_token
    ) {
      // manual sign up, need to activate email
      yield put(RegisterAction.registerSuccess());
      yield put(
        MessageAction.addMessage({
          error: false,
          message: registered_account.message
        })
      );
      browserHistory.push("/login");
    } else if (registered_account.auth_token && !registered_account.tfa_url) {
      yield call(updateOrganisationStateFromLoginData, registered_account);
      // email invite, auto login as email validated
      yield put(RegisterAction.registerSuccess());
      yield put(
        LoginAction.loginSuccess(createLoginSuccessObject(registered_account))
      );
      yield call(storeSessionToken, registered_account.auth_token);
      yield call(authenticatePusher);
    } else if (registered_account.tfa_url) {
      yield call(storeSessionToken, registered_account.auth_token);
      yield put(
        LoginAction.loginPartial({
          error: registered_account.message,
          tfaURL: registered_account.tfa_url,
          tfaFailure: true
        })
      );
    } else if (registered_account.tfa_failure) {
      yield call(removeTFAToken); // something failed on the TFA logic
      yield call(storeSessionToken, registered_account.auth_token);
      yield put(
        LoginAction.loginPartial({
          error: registered_account.message,
          tfaURL: null,
          tfaFailure: true
        })
      );
      return registered_account;
    } else {
      yield put(RegisterAction.registerFailure(registered_account.message));
      yield put(LoginAction.loginFailure(registered_account.message));
    }
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);

    yield put(RegisterAction.registerFailure(error.message));
  }
}

function* watchRegisterRequest() {
  yield takeEvery(RegisterActionTypes.REGISTER_REQUEST, register);
}

function* activate({ payload }) {
  try {
    const activated_account = yield call(activateAPI, payload);

    if (activated_account.auth_token && !activated_account.tfa_url) {
      yield put(ActivateAccountAction.activateAccountSuccess());
      yield put(
        LoginAction.loginSuccess(createLoginSuccessObject(activated_account))
      );
      yield call(updateOrganisationStateFromLoginData, activated_account);
      yield call(storeSessionToken, activated_account.auth_token);
      yield call(authenticatePusher);
    } else if (activated_account.tfa_url) {
      yield call(storeSessionToken, activated_account.auth_token);
      yield put(
        LoginAction.loginPartial({
          error: activated_account.message,
          tfaURL: activated_account.tfa_url,
          tfaFailure: true
        })
      );
    } else if (activated_account.tfa_failure) {
      yield call(removeTFAToken); // something failed on the TFA logic
      yield call(storeSessionToken, registered_account.auth_token);
      yield put(
        LoginAction.loginPartial({
          error: activated_account.message,
          tfaURL: null,
          tfaFailure: true
        })
      );
      return activated_account;
    } else {
      yield put(
        ActivateAccountAction.activateAccountFailure(
          activated_account.statusText
        )
      );
    }
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put(ActivateAccountAction.activateAccountFailure(error.statusText));
  }
}

function* watchActivateRequest() {
  yield takeEvery(ActivateActionTypes.ACTIVATE_REQUEST, activate);
}

function* resetEmailRequest({ payload }) {
  try {
    yield call(requestResetEmailAPI, payload);
    yield put(ResetPasswordEmailAction.passwordResetEmailSuccess());
  } catch (error) {
    yield put(
      ResetPasswordEmailAction.passwordResetEmailFailure(error.statusText)
    );
  }
}

function* watchResetEmailRequest() {
  yield takeEvery(
    ResetPasswordEmailActionTypes.REQUEST_RESET_REQUEST,
    resetEmailRequest
  );
}

function* resetPassword({ payload }) {
  try {
    yield call(ResetPasswordAPI, payload);
    yield put(ResetPasswordAction.resetPasswordSuccess());
    yield put(LoginAction.logout());
  } catch (error) {
    yield put(ResetPasswordAction.resetPasswordFailure(error.statusText));
  }
}

function* watchResetPassword() {
  yield takeEvery(
    ResetPasswordActionTypes.RESET_PASSWORD_REQUEST,
    resetPassword
  );
}

function* userList() {
  try {
    const load_result = yield call(getUserList);

    yield call(updateStateFromAdmin, load_result.data);

    yield put(LoadAdminUserListAction.loadAdminUserListSuccess());
  } catch (error) {
    yield put(
      LoadAdminUserListAction.loadAdminUserListFailure(error.statusText)
    );
  }
}

function* watchLoadUserList() {
  yield takeEvery(
    LoadAdminUserListActionTypes.LOAD_ADMIN_USER_REQUEST,
    userList
  );
}

function* updateUserRequest({ payload }) {
  try {
    const result = yield call(updateUserAPI, payload);

    if (result.data) {
      yield call(updateStateFromAdmin, result.data);
    }

    yield put(EditAdminUserAction.editAdminUserSuccess());

    yield put(
      MessageAction.addMessage({ error: false, message: result.message })
    );
  } catch (error) {
    yield put(EditAdminUserAction.editAdminUserFailure(error));
    yield put(MessageAction.addMessage({ error: true, message: error }));
  }
}

function* watchUpdateUserRequest() {
  yield takeEvery(
    EditAdminUserActionTypes.EDIT_ADMIN_USER_REQUEST,
    updateUserRequest
  );
}

const getInviteState = state => state.adminUsers.invitesById;

function* deleteInvite({ payload }) {
  try {
    const result = yield call(deleteInviteAPI, payload);
    yield put(DeleteInviteAction.deleteInviteSuccess());

    // delete item from local state
    let inviteState = yield select(getInviteState);
    let invites = { ...inviteState };
    delete invites[payload.body.invite_id];

    yield put(InviteUserListAction.updateInviteUsers(invites));
    yield put(
      MessageAction.addMessage({ error: false, message: result.message })
    );
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put(DeleteInviteAction.deleteInviteFailure(error.message));
  }
}

function* watchDeleteInviteRequest() {
  yield takeEvery(DeleteInviteActionTypes.DELETE_INVITE_REQUEST, deleteInvite);
}

function* inviteUserRequest({ payload }) {
  try {
    const result = yield call(inviteUserAPI, payload);
    yield put(InviteUserAction.inviteUserSuccess());
    yield put(
      MessageAction.addMessage({ error: false, message: result.message })
    );
    browserHistory.push("/settings");
  } catch (fetch_error) {
    const error = yield call(handleError, fetch_error);
    yield put(InviteUserAction.inviteUserFailure(error.message));
  }
}

function* watchInviteUserRequest() {
  yield takeEvery(InviteUserActionTypes.INVITE_USER_REQUEST, inviteUserRequest);
}

function* validateTFA({ payload }) {
  try {
    const validateTFAresponse = yield call(ValidateTFAAPI, payload);

    yield put(ValidateTfaAction.validateTFASuccess());
    yield call(updateOrganisationStateFromLoginData, validateTFAresponse);
    yield call(storeTFAToken, validateTFAresponse.tfa_auth_token);
    yield put(
      LoginAction.loginSuccess(createLoginSuccessObject(validateTFAresponse))
    );
    yield call(authenticatePusher);

    return validateTFAresponse;
  } catch (error) {
    const response = yield call(handleError, error);

    yield put(ValidateTfaAction.validateTFAFailure(response.message));
  }
}

function* watchValidateTFA() {
  yield takeEvery(ValidateTfaActionTypes.VALIDATE_TFA_REQUEST, validateTFA);
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
    watchDeleteInviteRequest(),
    watchValidateTFA()
  ]);
}
