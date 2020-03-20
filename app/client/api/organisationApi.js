import { apiClient } from './apiClient';

export const loadOrganisationAPI = () =>
  apiClient({ url: '/me/organisation/', method: 'GET' });

export const editOrganisationAPI = ({ body, path }) =>
  apiClient({
    url: '/organisation/',
    method: 'PUT',
    body,
    path,
  });
