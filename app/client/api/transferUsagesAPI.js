import { apiClient } from './apiClient';

export const loadTransferUsagesAPI = () =>
  apiClient({ url: '/transfer_usage/', method: 'GET' });
