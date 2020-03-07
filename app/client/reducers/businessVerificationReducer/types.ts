export const UPDATE_ACTIVE_STEP = "UPDATE_ACTIVE_STEP";
export const RESET_ACTIVE_STEP_STATE = "RESET_ACTIVE_STEP_STATE";

interface ActiveStepPayload {
  activeStep: number;
  userId: string;
}

interface UpdateActiveStep {
  type: typeof UPDATE_ACTIVE_STEP;
  payload: ActiveStepPayload;
}

interface ResetActiveStepState {
  type: typeof RESET_ACTIVE_STEP_STATE;
}

export type ActiveStepState = UpdateActiveStep | ResetActiveStepState;

export const UPDATE_BUSINESS_VERIFICATION_STATE =
  "UPDATE_BUSINESS_VERIFICATION_STATE";
export const RESET_BUSINESS_VERIFICATION_STATE =
  "RESET_BUSINESS_VERIFICATION_STATE";

interface UpdateBusinessVerificationPayload {
  kyc_application: object[];
}

interface UpdateBusinessVerificationState {
  type: typeof UPDATE_BUSINESS_VERIFICATION_STATE;
  payload: UpdateBusinessVerificationPayload;
}

interface ResetBusinessVerificationState {
  type: typeof RESET_BUSINESS_VERIFICATION_STATE;
}

export type BusinessVerificationStateAction =
  | UpdateBusinessVerificationState
  | ResetBusinessVerificationState;

export const EDIT_BUSINESS_VERIFICATION_REQUEST =
  "EDIT_BUSINESS_VERIFICATION_REQUEST";
export const EDIT_BUSINESS_VERIFICATION_SUCCESS =
  "EDIT_BUSINESS_VERIFICATION_SUCCESS";
export const EDIT_BUSINESS_VERIFICATION_FAILURE =
  "EDIT_BUSINESS_VERIFICATION_FAILURE";

interface EditBusinessVerificationRequest {
  type: typeof EDIT_BUSINESS_VERIFICATION_REQUEST;
}

interface EditBusinessVerificationSuccess {
  type: typeof EDIT_BUSINESS_VERIFICATION_SUCCESS;
}

interface EditBusinessVerificationFailure {
  type: typeof EDIT_BUSINESS_VERIFICATION_FAILURE;
  error: string;
}

export type EditBusinessVerificationAction =
  | EditBusinessVerificationRequest
  | EditBusinessVerificationSuccess
  | EditBusinessVerificationFailure;

export const CREATE_BUSINESS_VERIFICATION_REQUEST =
  "CREATE_BUSINESS_VERIFICATION_REQUEST";
export const CREATE_BUSINESS_VERIFICATION_SUCCESS =
  "CREATE_BUSINESS_VERIFICATION_SUCCESS";
export const CREATE_BUSINESS_VERIFICATION_FAILURE =
  "CREATE_BUSINESS_VERIFICATION_FAILURE";

interface CreateBusinessVerifcationRequest {
  type: typeof CREATE_BUSINESS_VERIFICATION_REQUEST;
}

interface CreateBusinessVerifcationSuccess {
  type: typeof CREATE_BUSINESS_VERIFICATION_SUCCESS;
}

interface CreateBusinessVerifcationFailure {
  type: typeof CREATE_BUSINESS_VERIFICATION_FAILURE;
  error: string;
}

export type CreateBusinessVerifcationAction =
  | CreateBusinessVerifcationRequest
  | CreateBusinessVerifcationSuccess
  | CreateBusinessVerifcationFailure;

export const LOAD_BUSINESS_VERIFICATION_REQUEST =
  "LOAD_BUSINESS_VERIFICATION_REQUEST";
export const LOAD_BUSINESS_VERIFICATION_SUCCESS =
  "LOAD_BUSINESS_VERIFICATION_SUCCESS";
export const LOAD_BUSINESS_VERIFICATION_FAILURE =
  "LOAD_BUSINESS_VERIFICATION_FAILURE";

interface LoadBusinessVerificationRequest {
  type: typeof LOAD_BUSINESS_VERIFICATION_REQUEST;
}

interface LoadBusinessVerificationSuccess {
  type: typeof LOAD_BUSINESS_VERIFICATION_SUCCESS;
}

interface LoadBusinessVerificationFailure {
  type: typeof LOAD_BUSINESS_VERIFICATION_FAILURE;
  error: string;
}

export type LoadBusinessVerificationAction =
  | LoadBusinessVerificationRequest
  | LoadBusinessVerificationSuccess
  | LoadBusinessVerificationFailure;

export const UPLOAD_DOCUMENT_REQUEST = "UPLOAD_DOCUMENT_REQUEST";
export const UPLOAD_DOCUMENT_SUCCESS = "UPLOAD_DOCUMENT_SUCCESS";
export const UPLOAD_DOCUMENT_FAILURE = "UPLOAD_DOCUMENT_FAILURE";

interface UploadDocumentRequest {
  type: typeof UPLOAD_DOCUMENT_REQUEST;
}

interface UploadDocumentSuccess {
  type: typeof UPLOAD_DOCUMENT_SUCCESS;
}

interface UploadDocumentFailure {
  type: typeof UPLOAD_DOCUMENT_FAILURE;
  error: string;
}

export type UploadDocumentAction =
  | UploadDocumentRequest
  | UploadDocumentSuccess
  | UploadDocumentFailure;

export const CREATE_BANK_ACCOUNT_REQUEST = "CREATE_BANK_ACCOUNT_REQUEST";
export const CREATE_BANK_ACCOUNT_SUCCESS = "CREATE_BANK_ACCOUNT_SUCCESS";
export const CREATE_BANK_ACCOUNT_FAILURE = "CREATE_BANK_ACCOUNT_FAILURE";

interface CreateBankAccountRequest {
  type: typeof CREATE_BANK_ACCOUNT_REQUEST;
}

interface CreateBankAccountSuccess {
  type: typeof CREATE_BANK_ACCOUNT_SUCCESS;
}

interface CreateBankAccountFailure {
  type: typeof CREATE_BANK_ACCOUNT_FAILURE;
  error: string;
}

export type CreateBankAccountAction =
  | CreateBankAccountRequest
  | CreateBankAccountSuccess
  | CreateBankAccountFailure;

export const EDIT_BANK_ACCOUNT_REQUEST = "EDIT_BANK_ACCOUNT_REQUEST";
export const EDIT_BANK_ACCOUNT_SUCCESS = "EDIT_BANK_ACCOUNT_SUCCESS";
export const EDIT_BANK_ACCOUNT_FAILURE = "EDIT_BANK_ACCOUNT_FAILURE";

interface EditBankAccountRequest {
  type: typeof EDIT_BANK_ACCOUNT_REQUEST;
}

interface EditBankAccountSuccess {
  type: typeof EDIT_BANK_ACCOUNT_SUCCESS;
}

interface EditBankAccountFailure {
  type: typeof EDIT_BANK_ACCOUNT_FAILURE;
  error: string;
}

export type EditBankAccountAction =
  | EditBankAccountRequest
  | EditBankAccountSuccess
  | EditBankAccountFailure;
