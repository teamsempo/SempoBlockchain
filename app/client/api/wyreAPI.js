import { apiClient } from './apiClient';

export const loadExchangeRates = () => apiClient({url: '/wyre_rates/', method: 'GET'});

export const loadWyreAccountBalance = () => apiClient({url: '/wyre_account/', method: 'GET'});

export const createWyreTransferRequest = ({body}) => apiClient({url: '/wyre_transfer/', method: 'POST', body: body});
