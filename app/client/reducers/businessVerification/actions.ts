import { createAction, ActionsUnion } from "../../reduxUtils";
import { BusinessVerificationActionTypes } from "./types";
import {
  EditBusinessProfilePayload,
  CreateBankAccountPayload,
  LoadBusinessProfilePayload,
  CreateBusinessProfilePayload,
  EditBankAccountPayload
} from "./types";

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

export const createBusinessVerificationRequest = (
  payload: CreateBusinessProfilePayload
) =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BUSINESS_VERIFICATION_REQUEST,
    payload
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

export const loadBusinessVerificationRequest = (
  payload: LoadBusinessProfilePayload
) =>
  createAction(
    BusinessVerificationActionTypes.LOAD_BUSINESS_VERIFICATION_REQUEST,
    payload
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

export const editBusinessVerificationRequest = (
  payload: EditBusinessProfilePayload
) =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BUSINESS_VERIFICATION_REQUEST,
    payload
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

export const createBankAccountRequest = (payload: CreateBankAccountPayload) =>
  createAction(
    BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_REQUEST,
    payload
  );

export const createBankAccountSuccess = () =>
  createAction(BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_SUCCESS);

export const createBankAccountFailure = (error: any) =>
  createAction(BusinessVerificationActionTypes.CREATE_BANK_ACCOUNT_FAILURE, {
    error
  });

export const editBankAccountRequest = (payload: EditBankAccountPayload) =>
  createAction(
    BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_REQUEST,
    payload
  );

export const editBankAccountSuccess = () =>
  createAction(BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_SUCCESS);

export const editBankAccountFailure = (error: any) =>
  createAction(BusinessVerificationActionTypes.EDIT_BANK_ACCOUNT_FAILURE, {
    error
  });

export const BusinessVerificationAction = {
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
  resetActiveStep
};

export type BusinessVerificationAction = ActionsUnion<
  typeof BusinessVerificationAction
>;
