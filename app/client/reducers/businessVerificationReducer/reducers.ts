import { DEEEEEEP } from "../../utils";
import { combineReducers } from "redux";
import {
  ActiveStepState,
  UPDATE_ACTIVE_STEP,
  RESET_ACTIVE_STEP_STATE,
  BusinessVerificationStateAction,
  UPDATE_BUSINESS_VERIFICATION_STATE,
  RESET_BUSINESS_VERIFICATION_STATE,
  CreateBusinessVerifcationAction,
  CREATE_BUSINESS_VERIFICATION_REQUEST,
  CREATE_BUSINESS_VERIFICATION_SUCCESS,
  CREATE_BUSINESS_VERIFICATION_FAILURE,
  LoadBusinessVerificationAction,
  LOAD_BUSINESS_VERIFICATION_REQUEST,
  LOAD_BUSINESS_VERIFICATION_SUCCESS,
  LOAD_BUSINESS_VERIFICATION_FAILURE,
  EditBusinessVerificationAction,
  EDIT_BUSINESS_VERIFICATION_REQUEST,
  EDIT_BUSINESS_VERIFICATION_SUCCESS,
  EDIT_BUSINESS_VERIFICATION_FAILURE,
  UploadDocumentAction,
  UPLOAD_DOCUMENT_REQUEST,
  UPLOAD_DOCUMENT_SUCCESS,
  UPLOAD_DOCUMENT_FAILURE,
  CreateBankAccountAction,
  CREATE_BANK_ACCOUNT_REQUEST,
  CREATE_BANK_ACCOUNT_SUCCESS,
  CREATE_BANK_ACCOUNT_FAILURE,
  EditBankAccountAction,
  EDIT_BANK_ACCOUNT_REQUEST,
  EDIT_BANK_ACCOUNT_SUCCESS,
  EDIT_BANK_ACCOUNT_FAILURE
} from "./types";

interface StepState {
  activeStep: number;
  userId: null | string;
}

const initialStepState: StepState = {
  activeStep: -1,
  userId: null
};

export const stepState = (
  state = initialStepState,
  action: ActiveStepState
): StepState => {
  switch (action.type) {
    case UPDATE_ACTIVE_STEP:
      return {
        ...state,
        activeStep: action.payload.activeStep,
        userId: action.payload.userId || state.userId
      };
    case RESET_ACTIVE_STEP_STATE:
      return initialStepState;
    default:
      return state;
  }
};

// TODO: what's the exact shape of businessverificationstate
const initialBusinessVerificationState = {};
const businessVerificationState = (
  state = initialBusinessVerificationState,
  action: BusinessVerificationStateAction
) => {
  switch (action.type) {
    case UPDATE_BUSINESS_VERIFICATION_STATE:
      return DEEEEEEP(state, action.payload.kyc_application);
    case RESET_BUSINESS_VERIFICATION_STATE:
      return initialBusinessVerificationState;
    default:
      return state;
  }
};

interface RequestStatusState {
  isRequesting: boolean;
  error: null | string;
  success: boolean;
}

const initialCreateStatusState: RequestStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const createStatus = (
  state = initialCreateStatusState,
  action: CreateBusinessVerifcationAction
): RequestStatusState => {
  switch (action.type) {
    case CREATE_BUSINESS_VERIFICATION_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case CREATE_BUSINESS_VERIFICATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case CREATE_BUSINESS_VERIFICATION_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const initialLoadStatusState: RequestStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const loadStatus = (
  state = initialLoadStatusState,
  action: LoadBusinessVerificationAction
): RequestStatusState => {
  switch (action.type) {
    case LOAD_BUSINESS_VERIFICATION_REQUEST:
      return { ...state, isRequesting: true };
    case LOAD_BUSINESS_VERIFICATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case LOAD_BUSINESS_VERIFICATION_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const initialEditStatusState: RequestStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const editStatus = (
  state = initialEditStatusState,
  action: EditBusinessVerificationAction
): RequestStatusState => {
  switch (action.type) {
    case EDIT_BUSINESS_VERIFICATION_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case EDIT_BUSINESS_VERIFICATION_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case EDIT_BUSINESS_VERIFICATION_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

interface UploadStatusState {
  isUploading: boolean;
  error: null | string;
  success: boolean;
}

const initialUploadDocumentStatusState: UploadStatusState = {
  isUploading: false,
  error: null,
  success: false
};

export const uploadDocumentStatus = (
  state = initialUploadDocumentStatusState,
  action: UploadDocumentAction
): UploadStatusState => {
  switch (action.type) {
    case UPLOAD_DOCUMENT_REQUEST:
      return { ...state, isUploading: true };
    case UPLOAD_DOCUMENT_SUCCESS:
      return { ...state, isUploading: false, success: true };
    case UPLOAD_DOCUMENT_FAILURE:
      return { ...state, isUploading: false, error: action.error };
    default:
      return state;
  }
};

const initialCreateBankAccountStatus: RequestStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const createBankAccountStatus = (
  state = initialCreateBankAccountStatus,
  action: CreateBankAccountAction
): RequestStatusState => {
  switch (action.type) {
    case CREATE_BANK_ACCOUNT_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case CREATE_BANK_ACCOUNT_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case CREATE_BANK_ACCOUNT_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
    default:
      return state;
  }
};

const initialEditBankAccountStatus: RequestStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

export const editBankAccountStatus = (
  state = initialEditBankAccountStatus,
  action: EditBankAccountAction
): RequestStatusState => {
  switch (action.type) {
    case EDIT_BANK_ACCOUNT_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case EDIT_BANK_ACCOUNT_SUCCESS:
      return { ...state, isRequesting: false, success: true };
    case EDIT_BANK_ACCOUNT_FAILURE:
      return { ...state, isRequesting: false, error: action.error };
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
