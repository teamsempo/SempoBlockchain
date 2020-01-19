import {generateFormattedURL, getToken, handleResponse} from "../utils";

/**
 * Sempo apiClient
 *
 * @param url, STRING to be queried
 * @param method, ENUM of available HTTP codes
 * @param isAuthed, BOOLEAN,
 * @param query, OBJECT of key/value pairs to be parsed into a query string
 * @param body, OBJECT, body data to send to server
 * @param path, INTEGER, used for calling specific object ID i.e. /1/
 * @param errorHandling, BOOLEAN, only use FALSE for special use case for TFA/auth
 * @returns {Promise<Response>}
 */
export const apiClient = ({url, method=method.toUpperCase(), isAuthed=true, query=null, body=null, path=null, errorHandling=true}) => {
  if (['PUT', 'POST', 'GET'].indexOf(method) === -1) {
    throw Error('Method provided is not supported')
  }

  console.log('url',url, 'method',method, 'isAuthed',isAuthed, 'query',query, 'body',body, 'path',path, 'errorHandling',errorHandling);

  //todo: check which headers are needed for given method
  let headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  isAuthed ? headers['Authorization'] = getToken() : null;

  let data = {
    headers: headers,
    method: method,
  };
  method !== 'GET' ? data['body'] = JSON.stringify(body) : null;

  return fetch(generateFormattedURL(url, query, path), data).then(response => {
    return errorHandling ? handleResponse(response) : response.json();
  }).catch(error => {
    throw error;
  });
};