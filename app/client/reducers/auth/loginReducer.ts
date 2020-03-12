import {
  LOGIN_FAILURE,
  LOGIN_PARTIAL,
  LOGIN_REQUEST,
  LOGIN_SUCCESS,
  LoginAction,
  LOGOUT,
  REAUTH_REQUEST,
  UPDATE_ACTIVE_ORG
} from "./types";

interface LoginState {
  isLoggingIn: boolean;
  //TODO(refactor): what is token actually? seems to only be used in checking it's not null
  token: null | string;
  //TODO(refactor): is it number or string?
  userId: null | number;
  email: null | string;
  //TODO(refactor): is it number or string?
  vendorId: null | number;
  intercomHash: null | string;
  webApiVersion: null | string;
  organisationName: null | string;
  //TODO(refactor): is it number or string?
  organisationId: null | number;
  organisationToken: null | string;
  usdToSatoshiRate: null | number;
  error: null | string;
  tfaURL: null | string;
  tfaFailure: boolean;
  //TODO(refactor): what is this actually?
  organisations?: null | string[];
  requireTransferCardExists: null | boolean;
  adminTier?: string;
}

const initialLoginState: LoginState = {
  isLoggingIn: false,
  token: null,
  userId: null,
  email: null,
  vendorId: null,
  intercomHash: null,
  webApiVersion: null,
  organisationName: null,
  organisationId: null,
  organisationToken: null,
  organisations: null,
  requireTransferCardExists: null,
  usdToSatoshiRate: null,
  error: null,
  tfaURL: null,
  tfaFailure: false
};

export const login = (state = initialLoginState, action: LoginAction) => {
  switch (action.type) {
    case REAUTH_REQUEST:
    case LOGIN_REQUEST:
      return { ...state, isLoggingIn: true };
    case UPDATE_ACTIVE_ORG:
      return {
        ...state,
        organisationName: action.payload.organisationName,
        organisationId: action.payload.organisationId
      };
    case LOGIN_SUCCESS:
      return {
        ...state,
        isLoggingIn: false,
        token: action.token,
        userId: action.userId,
        vendorId: action.vendorId,
        intercomHash: action.intercomHash,
        webApiVersion: action.webApiVersion,
        organisationName: action.organisationName,
        organisationId: action.organisationId,
        organisationToken: action.organisationToken,
        organisations: action.organisations,
        requireTransferCardExists: action.requireTransferCardExists,
        email: action.email,
        adminTier: action.adminTier,
        usdToSatoshiRate: action.usdToSatoshiRate,
        tfaURL: null,
        tfaFailure: false
      };
    case LOGIN_PARTIAL:
      return {
        ...state,
        isLoggingIn: false,
        token: null,
        userId: null,
        intercomHash: null,
        webApiVersion: null,
        organisationName: null,
        organisationId: null,
        organisations: null,
        requireTransferCardExists: null,
        tfaURL: action.tfaURL,
        tfaFailure: action.tfaFailure,
        error: action.error || "unknown error"
      };
    case LOGIN_FAILURE:
      return {
        ...state,
        isLoggingIn: false,
        token: null,
        userId: null,
        error: action.error || "unknown error"
      };
    case LOGOUT:
      return initialLoginState;
    default:
      return state;
  }
};
