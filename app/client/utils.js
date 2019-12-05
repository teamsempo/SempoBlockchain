import {call} from "redux-saga/effects";
import merge from 'deepmerge';
import {LOGIN_FAILURE} from "./reducers/authReducer";
import {put} from "redux-saga/es/effects";

export function formatMoney(amount, decimalCount = window.CURRENCY_DECIMALS, decimal = ".", thousands = ",") {
  try {
    decimalCount = Math.abs(decimalCount);
    decimalCount = isNaN(decimalCount) ? 2 : decimalCount;

    const negativeSign = amount < 0 ? "-" : "";

    let i = parseInt(amount = Math.abs(Number(amount) || 0).toFixed(decimalCount)).toString();
    let j = (i.length > 3) ? i.length % 3 : 0;

    return negativeSign + (j ? i.substr(0, j) + thousands : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thousands) + (decimalCount ? decimal + Math.abs(amount - i).toFixed(decimalCount).slice(2) : "") + ' ' + window.CURRENCY_NAME;
  } catch (e) {
    console.log(e)
  }
}

const overwriteMerge = (destinationArray, sourceArray) => sourceArray;

export function DEEEEEEP(parent_object, child_object_to_add) {
  // update object state data with new data, while keeping untouched old data, overwrite array
  return merge(parent_object, child_object_to_add, { arrayMerge: overwriteMerge })
}

export function addCreditTransferIdsToTransferAccount(parent_object, child_object_to_add) {
  // update object state data with new data, while keeping untouched old data, merge arrays
  return merge(parent_object, child_object_to_add)
}

export const generateQueryString = (query) => {
  let query_string = '?';

  if (query) {
    Object.keys(query).map(query_key => {
      let string_term = query_key + '=' + query[query_key] + '&';
      query_string = query_string.concat(string_term)
    });
  }

  let orgId = getOrgId();
  var response_string = query_string + `org=${orgId}&`;

  return response_string.slice(0, -1);
};


export const handleResponse = (response) => {
  if (response.ok) {
    return response.json();
  }
  return Promise.reject(response)
};


export function* handleError(error)  {

  const status = error.statusText;

  try {
    const json = yield call(extractJson, error);
    var message = json.message
  } catch (parse_error) {
    message = "Something went wrong."
  }

  if (error.status === 401) {
    yield put({type: LOGIN_FAILURE, error: message})
  }

  return {message, status}
};

const extractJson = (error) => {
    return error.json()
};

export const storeOrgid = (orgId) => {
  localStorage.setItem('orgId', orgId);
};

export const removeOrgId = (orgId) => {
  localStorage.removeItem('orgId')
};

export const getOrgId = () => {
  try {
    return localStorage.getItem('orgId')
  } catch (err) {
    removeOrgId();
    return null
  }
};

export const storeSessionToken = (token) => {
  localStorage.setItem('sessionToken', token);
};

export const  removeSessionToken = () => {
  localStorage.removeItem('sessionToken');
};

export const storeTFAToken = (token) => {
  localStorage.setItem('TFAToken', token);
};

export const  removeTFAToken = () => {
  localStorage.removeItem('TFAToken');
};

export const getTFAToken = () => {
  try {
    return localStorage.getItem('TFAToken')
  } catch (err) {
    removeTFAToken();
    return null
  }
}

export const getToken = () => {
  try {
    let sessionToken = localStorage.getItem('sessionToken');
    let TFAToken = localStorage.getItem('TFAToken');

    if (TFAToken) {
      return sessionToken + '|' + TFAToken
    }

    return sessionToken;
  } catch (err) {
    removeSessionToken();
    return ''
  }
};

export const replaceUnderscores = (stringlike) => {
  if (stringlike) {
      return (stringlike).toString().replace(/_/g," ")
  } else {
    return ""
  }
};
