import {generateFormattedURL, getToken, handleResponse} from "../utils";


export const apiClient = ({url, method=method.toUpperCase(), isAuthed=true, query=null, body=null, path=null}) => {
  //todo: check which headers are needed for given method
  let headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  isAuthed ? headers['Authorization'] = getToken() : null;

  //todo: check method is supported in ['PUT', 'POST', 'GET'], else raise error
  // if (method !==)

  return fetch(generateFormattedURL(url, query, path), {
    headers: headers,
    method: method,
  }).then(response => {
    return handleResponse(response)
  }).catch(error => {
    throw error;
  });
};