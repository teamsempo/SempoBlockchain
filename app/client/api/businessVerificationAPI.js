import { getToken, handleResponse, generateQueryString } from '../utils'

export const loadBusinessVerificationAPI = () => {
    return fetch('/api/kyc_application/', {
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
  return fetch('/api/kyc_application/', {
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
  if (path) {
    var URL = `/api/kyc_application/${path}/`;
  } else {
    URL = '/api/kyc_application/';
  }

  return fetch(URL, {
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

  return fetch("/api/document_upload/", {
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
  return fetch('/api/bank_account/', {
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
  if (path) {
    var URL = `/api/bank_account/${path}/`;
  } else {
    URL = '/api/bank_account/';
  }

  return fetch(URL, {
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
