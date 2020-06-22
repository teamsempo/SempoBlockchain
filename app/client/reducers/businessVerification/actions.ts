import { createAction, ActionsUnion } from "../../reduxUtils";
import { BusinessVerificationActionTypes } from "./types";

interface EditBusinessProfilePayload {
  body: any;
  path: string;
}

// Actions
export const editBusinessProfile = (payload: EditBusinessProfilePayload) =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_REQUEST,
    payload
  );

interface LoadBusinessProfilePayload {
  query: any;
}

export const loadBusinessProfile = (payload: LoadBusinessProfilePayload) =>
  createAction(
    BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_REQUEST,
    payload
  );

interface CreateBusinessProfilePayload {
  body: any;
}

export const createBusinessProfile = (payload: CreateBusinessProfilePayload) =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_REQUEST,
    payload
  );

interface DocumentDetails {
  document: any;
  reference: any;
  kyc_application: any;
}

interface UploadDocumentPayload {
  body: DocumentDetails;
}

interface CreateBankAccountPayload {
  body: any;
}

export const createBankAccount = (payload: CreateBankAccountPayload) =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_REQUEST,
    payload
  );

interface EditBankAccountPayload {
  body: any;
  path: string;
}

export const editBankAccount = (payload: EditBankAccountPayload) =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_REQUEST,
    payload
  );

export const updateActiveStep = (activeStep: number, userId?: number) =>
  createAction(BusinessVerificationActionTypes.UPDATE_ACTIVE_STEP, {
    activeStep,
    userId
  });

export const resetActiveStep = () =>
  createAction(BusinessVerificationActionTypes.RESET_ACTIVE_STEP_STATE);

export const updateBusinessVerificationState = (kyc_application: any) =>
  createAction(
    BusinessVerificationActionTypes.UPDATE_BUSINESS_VERIFICATION_STATE,
    { kyc_application }
  );

export const resetBusinessVerificationState = () =>
  createAction(
    BusinessVerificationActionTypes.RESET_BUSINESS_VERIFICATION_STATE
  );

export const createBusinessVerificationRequest = () =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_REQUEST
  );

export const createBusinessVerificationSuccess = () =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_SUCCESS
  );

export const createBusinessVerificationFailure = (error: any) =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_FAILURE,
    { error }
  );

export const loadBusinessVerificationRequest = () =>
  createAction(
    BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_REQUEST
  );

export const loadBusinessVerificationSuccess = () =>
  createAction(
    BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_SUCCESS
  );

export const loadBusinessVerificationFailure = (error: any) =>
  createAction(
    BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_FAILURE,
    { error }
  );

export const editBusinessVerificationRequest = () =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_REQUEST
  );

export const editBusinessVerificationSuccess = () =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_SUCCESS
  );

export const editBusinessVerificationFailure = (error: any) =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_FAILURE,
    { error }
  );

export const uploadDocumentRequest = () =>
  createAction(BusinessVerificationActionTypes.UPLOAD_DOCUMENT_REQUEST);

export const uploadDocumentSuccess = () =>
  createAction(BusinessVerificationActionTypes.UPLOAD_DOCUMENT_SUCCESS);

export const uploadDocumentFailure = (error: any) =>
  createAction(BusinessVerificationActionTypes.UPLOAD_DOCUMENT_FAILURE, {
    error
  });

export const createBankAccountRequest = () =>
  createAction(BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_REQUEST);

export const createBankAccountSuccess = () =>
  createAction(BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_SUCCESS);

export const createBankAccountFailure = (error: any) =>
  createAction(BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_FAILURE, {
    error
  });

export const editBankAccountRequest = () =>
  createAction(BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_REQUEST);

export const editBankAccountSuccess = () =>
  createAction(BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_SUCCESS);

export const editBankAccountFailure = (error: any) =>
  createAction(BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_FAILURE, {
    error
  });

export const BusinessVerificationAction = {
  editBusinessProfile,
  loadBusinessProfile,
  createBusinessProfile,
  updateBusinessVerificationState,
  resetBusinessVerificationState,
  createBusinessVerificationRequest,
  createBusinessVerificationFailure,
  createBusinessVerificationSuccess,
  loadBusinessVerificationRequest,
  loadBusinessVerificationFailure,
  loadBusinessVerificationSuccess,
  editBusinessVerificationRequest,
  editBusinessVerificationFailure,
  editBusinessVerificationSuccess,
  uploadDocumentRequest,
  uploadDocumentSuccess,
  uploadDocumentFailure,
  createBankAccountRequest,
  createBankAccountSuccess,
  createBankAccountFailure,
  editBankAccountRequest,
  editBankAccountSuccess,
  editBankAccountFailure,
  updateActiveStep,
  resetActiveStep,
  createBankAccount,
  editBankAccount
};

export type BusinessVerificationAction = ActionsUnion<
  typeof BusinessVerificationAction
>;
