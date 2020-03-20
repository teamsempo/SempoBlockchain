import { apiClient } from './apiClient';

export const uploadSpreadsheetAPI = ({ body }) =>
  apiClient({
    url: '/spreadsheet/upload/',
    method: 'POST',
    isForm: true,
    body,
  });

export const saveDatasetAPI = ({ body }) =>
  apiClient({ url: '/dataset/', method: 'POST', body });

export const loadDatasetListAPI = () =>
  apiClient({ url: '/dataset/', method: 'GET' });
