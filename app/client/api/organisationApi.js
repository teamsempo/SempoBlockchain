import { apiClient } from './apiClient';

// Load Organisation
export const loadOrganisationAPI = () => apiClient({url: '/me/organisation/', method: 'GET'});
