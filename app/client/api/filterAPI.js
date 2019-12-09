import {generateFormattedURL, getToken, handleResponse} from '../utils'

// Load Filters
export const loadFiltersAPI = () => {
    return fetch(generateFormattedURL('/api/filters/'), {
        headers: {
          'Authorization': getToken(),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
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

// Create Filter
export const createFilterAPI = ({body}) => {
  return fetch(generateFormattedURL('/api/filters/'), {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify(body)
  })
  .then(response => {
      return handleResponse(response);
  })
  .catch(error => {
      throw error;
  })
};
