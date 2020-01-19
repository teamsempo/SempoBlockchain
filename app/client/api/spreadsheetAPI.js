import {generateFormattedURL, getToken, handleResponse} from '../utils'
import {apiClient} from "./apiClient";

//todo: generic form handler
export const uploadSpreadsheetAPI= (spreadsheet, preview_id) => {

  const formData = new FormData();
  formData.append('spreadsheet', spreadsheet);
  formData.append('preview_id', preview_id);

  return fetch(generateFormattedURL('/spreadsheet/upload/'), {
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

export const saveDatasetAPI = ({body}) => apiClient({url: '/dataset/', method: 'POST', body: body});

export const loadDatasetListAPI = () => apiClient({url: '/dataset/', method: 'GET'});
