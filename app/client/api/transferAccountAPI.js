import {getToken, handleResponse, generateFormattedURL} from '../utils'

// Load Transfer Account Details
export const loadTransferAccountListAPI = ({query, path}) => {
    return fetch(generateFormattedURL('/api/transfer_account/', query , path), {
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
    return fetch(generateFormattedURL('/api/transfer_account/', null , path), {
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