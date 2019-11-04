import {getToken, handleResponse} from "../utils";

export const loadTransferUsagesAPI = () => {
  const URL = '/api/transfer_usage/';

  return fetch(URL, {
    headers: {
      'Authorization': getToken()
    },
    method: 'GET'
  })
    .then(response => {
      return handleResponse(response)
    })
    .catch(error => {
        throw error;
    })
};
