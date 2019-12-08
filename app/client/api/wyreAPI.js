import { getToken, handleResponse, generateQueryString } from '../utils'

export const loadExchangeRates = () => {
    const query_string = generateQueryString();
    const URL = `/api/wyre_rates/${query_string}`;

    return fetch(URL, {
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
    const query_string = generateQueryString();
    const URL = `/api/wyre_account/${query_string}`;

    return fetch(URL, {
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
  const query_string = generateQueryString();
  const URL = `/api/wyre_transfer/${query_string}`;

  return fetch(URL, {
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