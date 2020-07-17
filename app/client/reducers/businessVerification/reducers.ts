import { DEEEEEEP } from "../../utils";
import { combineReducers } from "redux";
import { BusinessVerificationActionTypes } from "./types";
import { BusinessVerificationAction } from "./actions";

interface StepState {
  activeStep: number;
  userId?: number | null;
}

const initialStepState: StepState = { activeStep: -1, userId: null };

export const stepState = (
  state = initialStepState,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.UPDATE_ACTIVE_STEP:
      return {
        ...state,
        activeStep: action.payload.activeStep,
        userId: action.payload.userId || state.userId
      };
    case BusinessVerificationActionTypes.RESET_ACTIVE_STEP_STATE:
      return initialStepState;
    default:
      return state;
  }
};

const initialBusinessVerificationState = {};
const businessVerificationState = (
  state = initialBusinessVerificationState,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.UPDATE_BUSINESS_VERIFICATION_STATE:
      return DEEEEEEP(state, action.payload.kyc_application);
    case BusinessVerificationActionTypes.RESET_BUSINESS_VERIFICATION_STATE:
      return initialBusinessVerificationState;
    default:
      return state;
  }
};

const initialCreateStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const createStatus = (
  state = initialCreateStatusState,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

const initialLoadStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const loadStatus = (
  state = initialLoadStatusState,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_REQUEST:
      return { ...state, isRequesting: true };

    case BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };

    case BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };

    default:
      return state;
  }
};

export const initialEditStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const editStatus = (
  state = initialEditStatusState,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

const initialUploadDocumentStatus = {
  isUploading: false,
  error: null,
  success: false
};

const uploadDocumentStatus = (
  state = initialUploadDocumentStatus,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.UPLOAD_DOCUMENT_REQUEST:
      return { ...state, isUploading: true };

    case BusinessVerificationActionTypes.UPLOAD_DOCUMENT_SUCCESS:
      return { ...state, isUploading: false, success: true };

    case BusinessVerificationActionTypes.UPLOAD_DOCUMENT_FAILURE:
      return { ...state, isUploading: false, error: action.payload.error };

    default:
      return state;
  }
};

export const initialCreateBankAccountStatus = {
  isRequesting: false,
  error: null,
  success: false
};

export const createBankAccountStatus = (
  state = initialCreateBankAccountStatus,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

export const initialEditBankAccountStatus = {
  isRequesting: false,
  error: null,
  success: false
};

export const editBankAccountStatus = (
  state = initialEditBankAccountStatus,
  action: BusinessVerificationAction
) => {
  switch (action.type) {
    case BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_FAILURE:
      return { ...state, isRequesting: false, error: action.payload.error };
    default:
      return state;
  }
};

export const businessVerification = combineReducers({
  stepState,
  businessVerificationState,
  uploadDocumentStatus,
  createBankAccountStatus,
  editBankAccountStatus,
  createStatus,
  loadStatus,
  editStatus
});
