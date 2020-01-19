import { apiClient } from './apiClient';

import {getToken, handleResponse, generateFormattedURL} from '../utils'

export const loadBusinessVerificationAPI = ({query}) => apiClient({url: '/kyc_application/', method: 'GET', query: query});

export const createBusinessVerificationAPI = ({body}) => apiClient({url: '/kyc_application/', method: 'POST', body: body});

export const editBusinessVerificationAPI = ({body, path}) => apiClient({url: '/kyc_application/', method: 'PUT', body: body, path: path});

//todo: generic form handler
export const uploadDocumentAPI = ({ body }) => {

  const formData = new FormData();
  formData.append('document', body.document);
  formData.append('reference', body.reference);
  formData.append('kyc_application_id', body.kyc_application_id);

  return fetch(generateFormattedURL('/document_upload/'), {
    headers: {
      'Authorization': getToken()
    },
    method: "POST",
    body: formData
  }).then(response => {
    return handleResponse(response)
  }).catch(error => {
    throw error;
  })
};

export const createBankAccountAPI = ({body}) => apiClient({url: '/bank_account/', method: 'POST', body: body});

export const editBankAccountAPI = ({body, path}) => apiClient({url: '/bank_account/', method: 'PUT', body: body, path: path});
