import {generateFormattedURL, getToken, handleResponse} from "../utils";

export const loadTransferUsagesAPI = () => {
  return fetch(generateFormattedURL('/api/transfer_usage/'), {
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
