import { apiClient } from './apiClient';

// Load list of credit transfers
export const loadCreditTransferListAPI = ({query, path}) => apiClient({url: '/credit_transfer/', method: 'GET', query: query, path: path});

// Modify credit transfer
export const modifyTransferAPI = ({body, path}) => apiClient({url: '/credit_transfer/', method: 'PUT', body: body, path: path});

// Create new credit transfer
export const newTransferAPI = ({body}) => apiClient({url: '/credit_transfer/', method: 'POST', body: body});
