import { DEEEEEEP } from "../utils";
import { combineReducers } from "redux";

export const UPDATE_ACTIVE_STEP = 'UPDATE_ACTIVE_STEP';
export const RESET_ACTIVE_STEP_STATE = 'RESET_ACTIVE_STEP_STATE';
export const UPDATE_BUSINESS_VERIFICATION_STATE = 'UPDATE_BUSINESS_VERIFICATION_STATE';
export const RESET_BUSINESS_VERIFICATION_STATE = 'RESET_BUSINESS_VERIFICATION_STATE';

export const EDIT_BUSINESS_VERIFICATION_REQUEST = 'EDIT_BUSINESS_VERIFICATION_REQUEST';
export const EDIT_BUSINESS_VERIFICATION_SUCCESS = 'EDIT_BUSINESS_VERIFICATION_SUCCESS';
export const EDIT_BUSINESS_VERIFICATION_FAILURE = 'EDIT_BUSINESS_VERIFICATION_FAILURE';

export const CREATE_BUSINESS_VERIFICATION_REQUEST = 'CREATE_BUSINESS_VERIFICATION_REQUEST';
export const CREATE_BUSINESS_VERIFICATION_SUCCESS = 'CREATE_BUSINESS_VERIFICATION_SUCCESS';
export const CREATE_BUSINESS_VERIFICATION_FAILURE = 'CREATE_BUSINESS_VERIFICATION_FAILURE';

export const LOAD_BUSINESS_VERIFICATION_REQUEST = 'LOAD_BUSINESS_VERIFICATION_REQUEST';
export const LOAD_BUSINESS_VERIFICATION_SUCCESS = 'LOAD_BUSINESS_VERIFICATION_SUCCESS';
export const LOAD_BUSINESS_VERIFICATION_FAILURE = 'LOAD_BUSINESS_VERIFICATION_FAILURE';

export const UPLOAD_DOCUMENT_REQUEST = 'UPLOAD_DOCUMENT_REQUEST';
export const UPLOAD_DOCUMENT_SUCCESS = 'UPLOAD_DOCUMENT_SUCCESS';
export const UPLOAD_DOCUMENT_FAILURE = 'UPLOAD_DOCUMENT_FAILURE';

export const CREATE_BANK_ACCOUNT_REQUEST = 'CREATE_BANK_ACCOUNT_REQUEST';
export const CREATE_BANK_ACCOUNT_SUCCESS = 'CREATE_BANK_ACCOUNT_SUCCESS';
export const CREATE_BANK_ACCOUNT_FAILURE = 'CREATE_BANK_ACCOUNT_FAILURE';

export const EDIT_BANK_ACCOUNT_REQUEST = 'EDIT_BANK_ACCOUNT_REQUEST';
export const EDIT_BANK_ACCOUNT_SUCCESS = 'EDIT_BANK_ACCOUNT_SUCCESS';
export const EDIT_BANK_ACCOUNT_FAILURE = 'EDIT_BANK_ACCOUNT_FAILURE';

const initialStepState = {activeStep: -1, userId: null};
export const stepState = (state = initialStepState, action) => {
  switch (action.type) {
    case UPDATE_ACTIVE_STEP:
      return {...state, activeStep: action.activeStep, userId: action.userId};
    case RESET_ACTIVE_STEP_STATE:
      return initialStepState;
    default:
      return state
  }
};

const initialBusinessVerificationState = {};
const businessVerificationState = (state = initialBusinessVerificationState, action) => {
  switch (action.type) {
    case UPDATE_BUSINESS_VERIFICATION_STATE:
      return DEEEEEEP(state, action.kyc_application);
    case RESET_BUSINESS_VERIFICATION_STATE:
      return initialBusinessVerificationState;
    default:
      return state;
  }
};

const initialCreateStatusState = {
  isRequesting: false,
  error: null,
  success: false,
};

export const createStatus = (state = initialCreateStatusState, action) => {
  switch (action.type) {
    case CREATE_BUSINESS_VERIFICATION_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case CREATE_BUSINESS_VERIFICATION_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case CREATE_BUSINESS_VERIFICATION_FAILURE:
      return {...state, isRequesting: false, error: action.error};
    default:
      return state;
  }
};

const initialLoadStatusState = {
  isRequesting: false,
  error: null,
  success: false
};

const loadStatus = (state = initialLoadStatusState, action) => {
  switch (action.type) {
    case LOAD_BUSINESS_VERIFICATION_REQUEST:
      return {...state, isRequesting: true};

    case LOAD_BUSINESS_VERIFICATION_SUCCESS:
      return {...state, isRequesting: false, success: true};

    case LOAD_BUSINESS_VERIFICATION_FAILURE:
      return {...state, isRequesting: false, error: action.error};

    default:
      return state;
  }
};


export const initialEditStatusState = {
  isRequesting: false,
  error: null,
  success: false,
};

export const editStatus = (state = initialEditStatusState, action) => {
  switch (action.type) {
    case EDIT_BUSINESS_VERIFICATION_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case EDIT_BUSINESS_VERIFICATION_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case EDIT_BUSINESS_VERIFICATION_FAILURE:
      return {...state, isRequesting: false, error: action.error};
    default:
      return state;
  }
};

const initialUploadDocumentStatus = {
  isUploading: false,
  error: null,
  success: false
};

const uploadDocumentStatus = (state = initialUploadDocumentStatus, action) => {
  switch (action.type) {
    case UPLOAD_DOCUMENT_REQUEST:
      return {...state, isUploading: true};

    case UPLOAD_DOCUMENT_SUCCESS:
      return {...state, isUploading: false, success: true};

    case UPLOAD_DOCUMENT_FAILURE:
      return {...state, isUploading: false, error: action.error};

    default:
      return state;
  }
};


export const initialCreateBankAccountStatus = {
  isRequesting: false,
  error: null,
  success: false,
};

export const createBankAccountStatus = (state = initialCreateBankAccountStatus, action) => {
  switch (action.type) {
    case CREATE_BANK_ACCOUNT_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case CREATE_BANK_ACCOUNT_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case CREATE_BANK_ACCOUNT_FAILURE:
      return {...state, isRequesting: false, error: action.error};
    default:
      return state;
  }
};

export const initialEditBankAccountStatus = {
  isRequesting: false,
  error: null,
  success: false,
};

export const editBankAccountStatus = (state = initialEditBankAccountStatus, action) => {
  switch (action.type) {
    case EDIT_BANK_ACCOUNT_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case EDIT_BANK_ACCOUNT_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case EDIT_BANK_ACCOUNT_FAILURE:
      return {...state, isRequesting: false, error: action.error};
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
  editStatus,
});


// Actions
export const editBusinessProfile = (payload) => (
  {
    type: EDIT_BUSINESS_VERIFICATION_REQUEST,
    payload
  }
);

export const loadBusinessProfile = (payload) => (
  {
    type: LOAD_BUSINESS_VERIFICATION_REQUEST,
    payload
  }
);

export const createBusinessProfile = (payload) => (
  {
    type: CREATE_BUSINESS_VERIFICATION_REQUEST,
    payload
  }
);

export const uploadDocument = (payload) => (
  {
    type: UPLOAD_DOCUMENT_REQUEST,
    payload
  }
);

export const createBankAccount = (payload) => (
  {
    type: CREATE_BANK_ACCOUNT_REQUEST,
    payload
  }
);

export const editBankAccount = (payload) => (
  {
    type: EDIT_BANK_ACCOUNT_REQUEST,
    payload
  }
);
