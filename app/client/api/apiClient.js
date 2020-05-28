import {
  generateFormattedURL,
  getTFAToken,
  getToken,
  handleResponse
} from "../utils";

/**
 * Sempo apiClient
 *
 * @param url, STRING to be queried
 * @param method, ENUM of available HTTP codes
 * @param isAuthed, BOOLEAN,
 * @param isTFA, BOOLEAN,
 * @param isForm, BOOLEAN,
 * @param query, OBJECT of key/value pairs to be parsed into a query string
 * @param body, OBJECT, body data to send to server
 * @param path, INTEGER, used for calling specific object ID i.e. /1/
 * @param errorHandling, BOOLEAN, only use FALSE for special use case for TFA/auth
 * @returns {Promise<Response>}
 */
export const apiClient = ({
  url,
  method = method.toUpperCase(),
  isAuthed = true,
  isTFA = false,
  isForm = false,
  query = null,
  body = null,
  path = null,
  errorHandling = true
}) => {
  if (["PUT", "POST", "GET", "DELETE"].indexOf(method) === -1) {
    throw new Error("Method provided is not supported");
  }

  let formData;
  let headers = {};
  let request = {
    headers: headers,
    method: method
  };

  if (isForm) {
    formData = new FormData();
    Object.keys(body).map(key => {
      formData.append(key.toString(), body[key]);
    });
    method !== "GET" ? (request["body"] = formData) : null;
  } else {
    headers["Accept"] = "application/json";
    headers["Content-Type"] = "application/json";
    method !== "GET" ? (request["body"] = JSON.stringify(body)) : null;
  }
  isAuthed ? (headers["Authorization"] = getToken()) : null;
  isTFA ? (body["tfa_token"] = getTFAToken()) : null;

  return fetch(generateFormattedURL(url, query, path), request)
    .then(response => {
      return errorHandling ? handleResponse(response) : response.json();
    })
    .catch(error => {
      throw error;
    });
};
