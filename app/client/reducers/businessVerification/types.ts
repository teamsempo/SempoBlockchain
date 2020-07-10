export enum BusinessVerificationActionTypes {
  UPDATE_ACTIVE_STEP = "UPDATE_ACTIVE_STEP",
  RESET_ACTIVE_STEP_STATE = "RESET_ACTIVE_STEP_STATE",
  UPDATE_BUSINESS_VERIFICATION_STATE = "UPDATE_BUSINESS_VERIFICATION_STATE",
  RESET_BUSINESS_VERIFICATION_STATE = "RESET_BUSINESS_VERIFICATION_STATE",

  EDIT_BUSINESS_VERIFICATION_REQUEST = "EDIT_BUSINESS_VERIFICATION_REQUEST",
  EDIT_BUSINESS_VERIFICATION_SUCCESS = "EDIT_BUSINESS_VERIFICATION_SUCCESS",
  EDIT_BUSINESS_VERIFICATION_FAILURE = "EDIT_BUSINESS_VERIFICATION_FAILURE",

  CREATE_BUSINESS_VERIFICATION_REQUEST = "CREATE_BUSINESS_VERIFICATION_REQUEST",
  CREATE_BUSINESS_VERIFICATION_SUCCESS = "CREATE_BUSINESS_VERIFICATION_SUCCESS",
  CREATE_BUSINESS_VERIFICATION_FAILURE = "CREATE_BUSINESS_VERIFICATION_FAILURE",

  LOAD_BUSINESS_VERIFICATION_REQUEST = "LOAD_BUSINESS_VERIFICATION_REQUEST",
  LOAD_BUSINESS_VERIFICATION_SUCCESS = "LOAD_BUSINESS_VERIFICATION_SUCCESS",
  LOAD_BUSINESS_VERIFICATION_FAILURE = "LOAD_BUSINESS_VERIFICATION_FAILURE",

  UPLOAD_DOCUMENT_REQUEST = "UPLOAD_DOCUMENT_REQUEST",
  UPLOAD_DOCUMENT_SUCCESS = "UPLOAD_DOCUMENT_SUCCESS",
  UPLOAD_DOCUMENT_FAILURE = "UPLOAD_DOCUMENT_FAILURE",

  CREATE_BANK_ACCOUNT_REQUEST = "CREATE_BANK_ACCOUNT_REQUEST",
  CREATE_BANK_ACCOUNT_SUCCESS = "CREATE_BANK_ACCOUNT_SUCCESS",
  CREATE_BANK_ACCOUNT_FAILURE = "CREATE_BANK_ACCOUNT_FAILURE",

  EDIT_BANK_ACCOUNT_REQUEST = "EDIT_BANK_ACCOUNT_REQUEST",
  EDIT_BANK_ACCOUNT_SUCCESS = "EDIT_BANK_ACCOUNT_SUCCESS",
  EDIT_BANK_ACCOUNT_FAILURE = "EDIT_BANK_ACCOUNT_FAILURE"
}

export interface EditBusinessProfilePayload {
  body: any;
  path: number;
}

export interface EditBusinessSagaPayload {
  type: typeof BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_REQUEST;
  payload: EditBusinessProfilePayload;
}

export interface LoadBusinessProfilePayload {
  query: any;
}

export interface LoadBusinessProfileSagaPayload {
  type: typeof BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_REQUEST;
  payload: LoadBusinessProfilePayload;
}

export interface CreateBusinessProfilePayload {
  body: any;
}

export interface CreateBusinessProfileSagaPayload {
  type: typeof BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_REQUEST;
  payload: CreateBusinessProfilePayload;
}

export interface DocumentDetails {
  document: any;
  reference: any;
  kyc_application: any;
}

export interface UploadDocumentPayload {
  body: DocumentDetails;
}

export interface UploadDocumentSagaPayload {
  type: typeof BusinessVerificationActionTypes.UPLOAD_DOCUMENT_REQUEST;
  payload: UploadDocumentPayload;
}

export interface CreateBankAccountPayload {
  body: any;
}

export interface CreateBankAccountSagaPayload {
  type: typeof BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_REQUEST;
  payload: CreateBankAccountPayload;
}

export interface EditBankAccountPayload {
  body: any;
  path: number;
}

export interface EditBankAccountSagaPayload {
  type: typeof BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_REQUEST;
  payload: EditBankAccountPayload;
}
