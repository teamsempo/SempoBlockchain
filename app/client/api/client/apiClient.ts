import {
  generateFormattedURL,
  getTFAToken,
  getToken,
  handleResponse
} from "../../utils";

import { ApiClientType } from "./types";

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
 * @returns {Promise<T>}
 */
export function apiClient<T>({
  url,
  method,
  isAuthed = true,
  isTFA = false,
  isForm = false,
  query = null,
  body = null,
  path = null,
  errorHandling = true
}: ApiClientType): Promise<T> {
  let formData: FormData;
  let headers: HeadersInit = {};
  let request: RequestInit = {
    headers: headers,
    method: method
  };

  if (isForm) {
    if (body === null) {
      throw new Error("Body cannot be null when apiClient isForm is true");
    }
    formData = new FormData();
    Object.keys(body).map((key: string) => {
      formData.append(key.toString(), body[key]);
    });
    method !== "GET" ? (request["body"] = formData) : null;
  } else {
    headers["Accept"] = "application/json";
    headers["Content-Type"] = "application/json";
    method !== "GET" ? (request["body"] = JSON.stringify(body)) : null;
  }

  let authToken = getToken();
  authToken = authToken === null ? "" : authToken;
  isAuthed ? (headers["Authorization"] = authToken) : null;

  if (isAuthed) {
    let authToken = getToken();
    authToken = authToken === null ? "" : authToken;
    headers["Authorization"] = authToken;
  }

  if (isTFA) {
    if (body === null) {
      throw new Error("Body cannot be null when apiClient isTFA is true");
    }
    let tfaToken = getTFAToken();
    tfaToken = tfaToken === null ? "" : tfaToken;
    body["tfa_token"] = tfaToken;
  }

  return fetch(generateFormattedURL(url, query, path), request)
    .then(response => {
      return errorHandling
        ? handleResponse(response)
        : (response.json() as Promise<T>);
    })
    .catch(error => {
      throw error;
    });
}
