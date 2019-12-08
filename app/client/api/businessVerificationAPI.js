import { getToken, handleResponse, generateQueryString } from '../utils'

export const loadBusinessVerificationAPI = () => {
    const query_string = generateQueryString();
    const URL = `/api/kyc_application/${query_string}`;

    return fetch(URL, {
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
  const query_string = generateQueryString();
  const URL = `/api/kyc_application/${query_string}`;

  return fetch(URL, {
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
  var query_string = generateQueryString();
  if (path) {
    var URL = `/api/kyc_application/${path}/${query_string}`;
  } else {
    URL = `/api/kyc_application/${query_string}`;
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

  const query_string = generateQueryString();
  const URL = `/api/document_upload/${query_string}`;

  return fetch(URL, {
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
  const query_string = generateQueryString();
  const URL = `/api/bank_account/${query_string}`;

  return fetch(URL, {
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
  var query_string = generateQueryString();
  if (path) {
    var URL = `/api/bank_account/${path}/${query_string}`;
  } else {
    URL = `/api/bank_account/${query_string}`;
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
