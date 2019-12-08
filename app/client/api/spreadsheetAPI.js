import {generateQueryString, getToken, handleResponse} from '../utils'

export const uploadSpreadsheetAPI= (spreadsheet, preview_id) => {

  const formData = new FormData();
  formData.append('spreadsheet', spreadsheet);
  formData.append('preview_id', preview_id);

  const query_string = generateQueryString();
  const URL = `/api/spreadsheet/upload/${query_string}`;

  return fetch(URL, {
    headers: {
      'Authorization': getToken()
    },
    method: "POST",
    body: formData
  }).then(response => {
    return handleResponse(response)
  }).catch(error => {
    throw error;
  })
};

export const saveDatasetAPI= (dataset) => {
  const query_string = generateQueryString();
  const URL = `/api/dataset/${query_string}`;

  return fetch(URL, {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: "POST",
    body: JSON.stringify(dataset)
  }).then(response => {
    return handleResponse(response)
  }).catch(error => {
    throw error;
  })
};

export const loadDatasetListAPI= () => {
  const query_string = generateQueryString();
  const URL = `/api/dataset/${query_string}`;

  return fetch(URL , {
    headers: {
      'Authorization': getToken()
    },
    method: 'GET'
    })
    .then(response => {
      return handleResponse(response)
    })
    .catch(error => {
      throw error;
    })
};
