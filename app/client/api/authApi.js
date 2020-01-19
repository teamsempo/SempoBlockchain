import {handleResponse, getToken, getTFAToken, getOrgId, generateFormattedURL} from '../utils'
import { startConfiguration } from 'pusher-redux';
import {apiClient} from "./apiClient";

//Auth API Call
export const requestApiToken = ({body}) => {
  body['tfa_token'] = getTFAToken();
  return fetch('/api/v1/auth/request_api_token/' , {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify(body)
    })
    .then(response => {
      // special use case for TFA
      return response.json();
    })
    .catch(error => {
      throw error;
    })
};

export const refreshApiToken = () => {
  let orgId = getOrgId();
  if (orgId !== null) {
    var URL = `/api/v1/auth/refresh_api_token/?org=${orgId}`
  } else {
    URL = '/api/v1/auth/refresh_api_token/'
  }

  return fetch(URL ,{
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json'
    },
    method: 'get'
  })
  .then(response => {

      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};

export const registerAPI = ({body}) => {
  return fetch('/api/v1/auth/register/' , {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify(body)
    })
    .then(response => {
      // special use case for TFA
      return response.json();
    })
    .catch(error => {
      throw error;
    })
};

export const activateAPI = (activation_token) => {
  return fetch('/api/v1/auth/activate/' , {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify({
      'activation_token': activation_token
      })
    })
    .then(response => {
      // special use case for TFA
      return response.json();
    })
    .catch(error => {
      throw error;
    })
};

export const requestResetEmailAPI = (email) => {
  return fetch('/api/v1/auth/request_reset_email/' , {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify({
      'email': email
      })
    })
    .then(response => {
      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};

export const GetTFAAPI = () => {
  return fetch('/api/v1/auth/tfa/' , {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
    },
    method: 'GET',
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};


export const ValidateTFAAPI = (payload) => {
  return fetch('/api/v1/auth/tfa/' , {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify(payload)
    })
    .then(response => {
      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};



export const ResetPasswordAPI = (payload) => {
  return fetch('/api/v1/auth/reset_password/' , {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify(payload)
    })
    .then(response => {
      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};

export const authenticatePusher = () => {
  console.log('authenticating pusher');
  startConfiguration({
    auth: {
      headers: {
        'Authorization': getToken()
      }
    },
    authEndpoint: generateFormattedURL('/pusher/auth')
  });
};

export const getUserList = () => apiClient({url: '/auth/permissions/', method: 'GET'});

export const updateUserAPI = ({body, query}) => apiClient({url: '/auth/permissions/', method: 'PUT', body: body, query: query});

export const inviteUserAPI = ({body}) => apiClient({url: '/auth/permissions/', method: 'POST', body: body});
