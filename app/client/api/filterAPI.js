import {generateQueryString, getToken, handleResponse} from '../utils'

// Load Filters
export const loadFiltersAPI = () => {
    const query_string = generateQueryString();
    var URL = `/api/filters/${query_string}`;

    return fetch(URL, {
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
  const query_string = generateQueryString();
  var URL = `/api/filters/${query_string}`;

  return fetch(URL, {
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
