import {getToken, handleResponse, generateFormattedURL} from '../utils'

// Load User Details
export const loadUserAPI = ({query, path}) => {
    return fetch(generateFormattedURL('/api/user/', query, path), {
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
  return fetch(generateFormattedURL('/api/user/'), {
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
    return fetch(generateFormattedURL('/api/user/', null, path), {
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