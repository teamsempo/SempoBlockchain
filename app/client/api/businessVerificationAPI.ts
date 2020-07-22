import { apiClient } from "./client/apiClient";
import {
  LoadBusinessProfilePayload,
  CreateBusinessProfilePayload,
  EditBusinessProfilePayload,
  UploadDocumentPayload,
  CreateBankAccountPayload,
  EditBankAccountPayload
} from "../reducers/businessVerification/types";

export const loadBusinessVerificationAPI = ({
  query
}: LoadBusinessProfilePayload) =>
  apiClient({ url: "/kyc_application/", method: "GET", query: query });

export const createBusinessVerificationAPI = ({
  body
}: CreateBusinessProfilePayload) =>
  apiClient({ url: "/kyc_application/", method: "POST", body: body });

export const editBusinessVerificationAPI = ({
  body,
  path
}: EditBusinessProfilePayload) =>
  apiClient({
    url: "/kyc_application/",
    method: "PUT",
    body: body,
    path: path
  });

export const uploadDocumentAPI = ({ body }: UploadDocumentPayload) =>
  apiClient({
    url: "/document_upload/",
    method: "POST",
    isForm: true,
    body: body
  });

export const createBankAccountAPI = ({ body }: CreateBankAccountPayload) =>
  apiClient({ url: "/bank_account/", method: "POST", body: body });

export const editBankAccountAPI = ({ body, path }: EditBankAccountPayload) =>
  apiClient({ url: "/bank_account/", method: "PUT", body: body, path: path });
