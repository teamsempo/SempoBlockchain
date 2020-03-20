import { apiClient } from './apiClient';

export const loadBusinessVerificationAPI = ({ query }) =>
  apiClient({ url: '/kyc_application/', method: 'GET', query });

export const createBusinessVerificationAPI = ({ body }) =>
  apiClient({ url: '/kyc_application/', method: 'POST', body });

export const editBusinessVerificationAPI = ({ body, path }) =>
  apiClient({
    url: '/kyc_application/',
    method: 'PUT',
    body,
    path,
  });

export const uploadDocumentAPI = ({ body }) =>
  apiClient({
    url: '/document_upload/',
    method: 'POST',
    isForm: true,
    body,
  });

export const createBankAccountAPI = ({ body }) =>
  apiClient({ url: '/bank_account/', method: 'POST', body });

export const editBankAccountAPI = ({ body, path }) =>
  apiClient({
    url: '/bank_account/',
    method: 'PUT',
    body,
    path,
  });
