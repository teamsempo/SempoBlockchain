import { apiClient } from './apiClient';

// Load Filters
export const loadFiltersAPI = ({query, path}) => apiClient({url: '/filters/', method: 'GET', query: query, path: path});

// Create Filter
export const createFilterAPI = ({body}) => apiClient({url: '/filters/', method: 'POST', body: body});
