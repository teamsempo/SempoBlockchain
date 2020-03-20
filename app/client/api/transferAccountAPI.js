import { apiClient } from './apiClient';

export const loadTransferAccountListAPI = ({ query, path }) =>
  apiClient({
    url: '/transfer_account/',
    method: 'GET',
    query,
    path,
  });

export const editTransferAccountAPI = ({ body, path }) =>
  apiClient({
    url: '/transfer_account/',
    method: 'PUT',
    body,
    path,
  });
