import { getToken, handleResponse, generateFormattedURL } from '../utils'

export const loadCreditTransferListAPI = ({query , path}) => {
    return fetch(generateFormattedURL('/api/credit_transfer/', query , path), {
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
  return fetch(generateFormattedURL('/api/credit_transfer/', null , path), {
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
  return fetch(generateFormattedURL('/api/credit_transfer/'), {
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
