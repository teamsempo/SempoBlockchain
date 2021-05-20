import { LoginAction } from "./actions";
import { LoginActionTypes } from "./types";

export interface LoginState {
  isLoggingIn: boolean;
  token: null | string;
  userId: null | number;
  email: null | string;
  intercomHash: null | string;
  webApiVersion: null | string;
  organisationId: null | number;
  organisationIds: null | string[];
  usdToSatoshiRate: null | number;
  error: null | string;
  tfaURL: null | string;
  tfaFailure: boolean;
  adminTier?: string;
}

const initialLoginState: LoginState = {
  isLoggingIn: false,
  token: null,
  userId: null,
  email: null,
  intercomHash: null,
  webApiVersion: null,
  organisationId: null,
  organisationIds: null,
  usdToSatoshiRate: null,
  error: null,
  tfaURL: null,
  tfaFailure: false
};

export const login = (state = initialLoginState, action: LoginAction) => {
  switch (action.type) {
    case LoginActionTypes.REAUTH_REQUEST:
    case LoginActionTypes.LOGIN_REQUEST:
      return { ...state, isLoggingIn: true };
    case LoginActionTypes.UPDATE_ACTIVE_ORG:
      return {
        ...state
        // organisationIds: action.payload.organisationIds
      };
    case LoginActionTypes.LOGIN_SUCCESS:
      return {
        ...state,
        isLoggingIn: false,
        token: action.payload.token,
        userId: action.payload.userId,
        intercomHash: action.payload.intercomHash,
        webApiVersion: action.payload.webApiVersion,
        organisationId: action.payload.organisationId,
        organisationIds: action.payload.organisationIds,
        email: action.payload.email,
        adminTier: action.payload.adminTier,
        usdToSatoshiRate: action.payload.usdToSatoshiRate,
        tfaURL: null,
        tfaFailure: false
      };
    case LoginActionTypes.LOGIN_PARTIAL:
      return {
        ...state,
        isLoggingIn: false,
        token: null,
        userId: null,
        intercomHash: null,
        webApiVersion: null,
        organisationId: null,
        tfaURL: action.payload.tfaURL,
        tfaFailure: action.payload.tfaFailure,
        error: action.payload.error || "unknown error"
      };
    case LoginActionTypes.LOGIN_FAILURE:
      return {
        ...state,
        isLoggingIn: false,
        token: null,
        userId: null,
        error: action.error || "unknown error"
      };
    case LoginActionTypes.API_LOGOUT:
      return initialLoginState;
    case LoginActionTypes.LOGOUT:
      return initialLoginState;
    default:
      return state;
  }
};
