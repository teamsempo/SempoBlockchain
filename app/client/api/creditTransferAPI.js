import { apiClient } from './apiClient';

export const loadCreditTransferListAPI = ({ query, path }) =>
  apiClient({
    url: '/credit_transfer/',
    method: 'GET',
    query,
    path,
  });

export const modifyTransferAPI = ({ body, path }) =>
  apiClient({
    url: '/credit_transfer/',
    method: 'PUT',
    body,
    path,
  });

export const newTransferAPI = ({ body }) =>
  apiClient({ url: '/credit_transfer/', method: 'POST', body });

export const loadCreditTransferStatsAPI = ({ query, path }) =>
  apiClient({
    url: '/credit_transfer/stats/',
    method: 'GET',
    query,
    path,
  });

export const loadCreditTransferFiltersAPI = ({ query, path }) =>
  apiClient({
    url: '/credit_transfer/filters/',
    method: 'GET',
    query,
    path,
  });
