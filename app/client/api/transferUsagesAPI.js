import {generateQueryString, getToken, handleResponse} from "../utils";

export const loadTransferUsagesAPI = () => {
  const query_string = generateQueryString();
  const URL = `/api/transfer_usage/${query_string}`;

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
