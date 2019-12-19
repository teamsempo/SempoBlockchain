import {getToken, handleResponse, generateQueryString, generateFormattedURL} from '../utils'

export const loadBusinessVerificationAPI = ({query}) => {
    return fetch(generateFormattedURL('/kyc_application/', query), {
      headers: {
          'Authorization': getToken(),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
      },
      method: 'GET',
      })
      .then(response => {
        return handleResponse(response)
      })
      .catch(error => {
        throw error;
      })
};

export const createBusinessVerificationAPI = ({body}) => {
  return fetch(generateFormattedURL('/kyc_application/'), {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify(body)
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};

export const editBusinessVerificationAPI = ({body, path}) => {
  return fetch(generateFormattedURL('/kyc_application/', null , path), {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'PUT',
    body: JSON.stringify(body)
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};


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


export const createBankAccountAPI = ({body}) => {
  return fetch(generateFormattedURL('/bank_account/'), {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify(body)
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};

export const editBankAccountAPI = ({body, path}) => {
  return fetch(generateFormattedURL('/bank_account/', null, path), {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'PUT',
    body: JSON.stringify(body)
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};
