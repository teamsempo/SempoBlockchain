import { getToken, handleResponse, generateQueryString } from '../utils'

// Load Transfer Account Details
export const loadTransferAccountListAPI = ({query, path}) => {
    if (query) {
        const query_string = generateQueryString(query);
        var URL = `/api/transfer_account/${query_string}`;
    } else if (path) {
        URL = `/api/transfer_account/${path}/`;
    } else {
        URL = '/api/transfer_account/';
    }

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

// Edit Transfer Account Details
export const editTransferAccountAPI = ({body, path}) => {
    if (path) {
        var URL = `/api/transfer_account/${path}/`;
    } else {
        URL = '/api/transfer_account/';
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