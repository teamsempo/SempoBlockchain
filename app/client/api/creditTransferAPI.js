import { apiClient } from './apiClient';

export const loadCreditTransferListAPI = ({query, path}) => apiClient({url: '/credit_transfer/', method: 'GET', query: query, path: path});

export const modifyTransferAPI = ({body, path}) => apiClient({url: '/credit_transfer/', method: 'PUT', body: body, path: path});

export const newTransferAPI = ({body}) => apiClient({url: '/credit_transfer/', method: 'POST', body: body});

export const loadCreditTransferStatsAPI = ({query, path}) => apiClient({url: '/credit_transfer/stats/', method: "GET", query: query, path: path});

export const loadCreditTransferFiltersAPI = ({query, path}) => apiClient({url: '/credit_transfer/filters/', method: "GET", query: query, path: path})