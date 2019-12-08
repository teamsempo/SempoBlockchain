import { getToken, handleResponse, generateQueryString } from '../utils'

// Load User Details
export const loadUserAPI = ({query, path}) => {
    var query_string = generateQueryString(query);
    if (query) {
        var URL = `/api/user/${query_string}`;
    } else if (path) {
        URL = `/api/user/${path}/${query_string}`;
    } else {
        URL = `/api/user/${query_string}`;
    }

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

// Create at User with Auth
export const createUserAPI = ({body}) => {
  const query_string = generateQueryString();
  var URL = `/api/user/${query_string}`;

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

// Edit Transfer Account Details
export const editUserAPI = ({body, path}) => {
    var query_string = generateQueryString();
    if (path) {
        var URL = `/api/user/${path}/${query_string}`;
    } else {
        URL = `/api/user/${query_string}`;
    }

    return fetch(URL, {
        headers: {
          'Authorization': getToken(),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        method: 'PUT',
        body: JSON.stringify(body)
    })
    .then(response => {
        return handleResponse(response)
    })
    .catch(error => {
        throw error;
    })
};