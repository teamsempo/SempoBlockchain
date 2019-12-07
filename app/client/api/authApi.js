import { handleResponse, storeSessionToken, removeSessionToken, getToken, getTFAToken, generateQueryString, getOrgId } from '../utils'
import { startConfiguration } from 'pusher-redux';

//Auth API Call
export const requestApiToken = ({body}) => {
  body['tfa_token'] = getTFAToken();
  return fetch('/api/auth/request_api_token/' , {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify(body)
    })
    .then(response => {
      return response.json();
    })
    .catch(error => {
      throw error;
    })
};

export const refreshApiToken = () => {
  let orgId = getOrgId();
  if (orgId !== null) {
    var URL = `/api/auth/refresh_api_token/?org=${orgId}`
  } else {
    URL = '/api/auth/refresh_api_token/'
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
  return fetch('/api/auth/register/' , {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'post',
    body: JSON.stringify(body)
    })
    .then(response => {
      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};

export const activateAPI = (activation_token) => {
  return fetch('/api/auth/activate/' , {
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
      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};

export const requestResetEmailAPI = (email) => {
  return fetch('/api/auth/request_reset_email/' , {
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
  return fetch('/api/auth/tfa/' , {
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
}


export const ValidateTFAAPI = (payload) => {
  return fetch('/api/auth/tfa/' , {
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
  return fetch('/api/auth/reset_password/' , {
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
    }
  });
};

export const getUserList = () => {
  const query_string = generateQueryString();
  var URL = `/api/auth/permissions/${query_string}`;

  return fetch(URL, {
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

export const updateUserAPI = ({body, query}) => {
  const query_string = generateQueryString(query);
  var URL = `/api/auth/permissions/${query_string}`;

  return fetch(URL, {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'PUT',
    body: JSON.stringify(body)
  }).then(response => {
      return response.json();
    })
    .catch(error => {
      throw error;
    })
};

export const inviteUserAPI = ({body}) => {
  const query_string = generateQueryString();
  var URL = `/api/auth/permissions/${query_string}`;

  return fetch(URL, {
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