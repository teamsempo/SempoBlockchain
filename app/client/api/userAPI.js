import { apiClient } from './apiClient';

export const loadUserAPI = ({ query, path }) =>
  apiClient({
    url: '/user/',
    method: 'GET',
    query,
    path,
  });

export const createUserAPI = ({ body }) =>
  apiClient({ url: '/user/', method: 'POST', body });

export const editUserAPI = ({ body, path }) =>
  apiClient({
    url: '/user/',
    method: 'PUT',
    body,
    path,
  });

export const resetPinAPI = ({ body }) =>
  apiClient({ url: '/user/reset_pin/', method: 'POST', body });
