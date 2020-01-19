import { apiClient } from './apiClient';

export const loadFiltersAPI = ({query, path}) => apiClient({url: '/filters/', method: 'GET', query: query, path: path});

export const createFilterAPI = ({body}) => apiClient({url: '/filters/', method: 'POST', body: body});
