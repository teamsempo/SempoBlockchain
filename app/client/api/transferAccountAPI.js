import { getToken, handleResponse, generateQueryString } from '../utils'

// Load Transfer Account Details
export const loadTransferAccountListAPI = ({query, path}) => {
    var query_string = generateQueryString(query);
    if (query) {
        var URL = `/api/transfer_account/${query_string}`;
    } else if (path) {
        URL = `/api/transfer_account/${path}/${query_string}`;
    } else {
        URL = `/api/transfer_account/${query_string}`;
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
    var query_string = generateQueryString();
    if (path) {
        var URL = `/api/transfer_account/${path}/${query_string}`;
    } else {
        URL = `/api/transfer_account/${query_string}`;
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