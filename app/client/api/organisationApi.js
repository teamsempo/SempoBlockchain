import {generateFormattedURL, getToken, handleResponse} from "../utils";

export const loadOrganisationAPI = () => {
  return fetch(generateFormattedURL('/me/organisation/'), {
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
