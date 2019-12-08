import { getToken, handleResponse, generateQueryString } from '../utils'

export const loadCreditTransferListAPI = ({query , path}) => {
    var query_string = generateQueryString(query);
    if (query) {
        var URL = `/api/credit_transfer/${query_string}`;
    } else if (path) {
        URL = `/api/credit_transfer/${path}/${query_string}`;
    } else {
        URL = `/api/credit_transfer/${query_string}`;
    }

    return fetch(URL, {
      headers: {
          'Authorization': getToken(),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
      },
      method: 'GET',
      // body: JSON.stringify({'transfer_account_id_list': transfer_account_id_list})
      })
      .then(response => {
        return handleResponse(response)
      })
      .catch(error => {
        throw error;
      })
};

export const modifyTransferAPI = ({body, path}) => {
  var query_string = generateQueryString();
  if (path) {
      var URL = `/api/credit_transfer/${path}/${query_string}`;
  } else {
      URL = `/api/credit_transfer/${query_string}`;
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

export const newTransferAPI = ({body}) => {
  const query_string = generateQueryString();
  var URL = `/api/credit_transfer/${query_string}`;

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
