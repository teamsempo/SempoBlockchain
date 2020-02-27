import { apiClient } from './apiClient';

export const loadSearchAPI = () => apiClient({url: '/search/', method: 'GET'});
