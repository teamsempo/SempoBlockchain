import {getToken, handleResponse, generateFormattedURL} from '../utils'

export const loadExchangeRates = () => {
    return fetch(generateFormattedURL('/api/wyre_rates/'), {
      headers: {
          'Authorization': getToken(),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
      },
      method: 'GET',
      })
      .then(response => {
        return handleResponse(response)
      })
      .catch(error => {
        throw error;
      })
};

export const loadWyreAccountBalance = () => {
    return fetch(generateFormattedURL('/api/wyre_account/'), {
      headers: {
          'Authorization': getToken(),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
      },
      method: 'GET',
      })
      .then(response => {
        return handleResponse(response)
      })
      .catch(error => {
        throw error;
      })
};


export const createWyreTransferRequest = ({body}) => {
  return fetch(generateFormattedURL('/api/wyre_transfer/'), {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify(body)
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};