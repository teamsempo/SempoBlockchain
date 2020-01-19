import { apiClient } from './apiClient';

// Load Transfer Account Details
export const loadTransferAccountListAPI = ({query, path}) => apiClient({url: '/transfer_account/', method: 'GET', query: query, path: path});


// Edit Transfer Account Details
export const editTransferAccountAPI = ({body, path}) => apiClient({url: '/transfer_account/', method: 'PUT', body: body, path: path});