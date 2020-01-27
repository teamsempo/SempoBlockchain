import { apiClient } from './apiClient';

export const loadCreditTransferListAPI = ({query, path}) => apiClient({url: '/credit_transfer/', method: 'GET', query: query, path: path});

export const modifyTransferAPI = ({body, path}) => apiClient({url: '/credit_transfer/', method: 'PUT', body: body, path: path});

export const newTransferAPI = ({body}) => apiClient({url: '/credit_transfer/', method: 'POST', body: body});
