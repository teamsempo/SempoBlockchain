import { call, put } from 'redux-saga/effects';
import merge from 'deepmerge';
import { LOGIN_FAILURE } from './reducers/auth/types';

import { store } from './app.jsx';
import { USER_FILTER_TYPE } from './constants';

export function formatMoney(
  amount,
  decimalCount,
  decimal = '.',
  thousands = ',',
  currency,
) {
  try {
    decimalCount = Math.abs(decimalCount);
    decimalCount = isNaN(decimalCount) ? 2 : decimalCount;

    const negativeSign = amount < 0 ? '-' : '';

    const i = parseInt(
      (amount = Math.abs(Number(amount) || 0).toFixed(decimalCount)),
    ).toString();
    const j = i.length > 3 ? i.length % 3 : 0;

    return `${negativeSign +
      (j ? i.substr(0, j) + thousands : '') +
      i.substr(j).replace(/(\d{3})(?=\d)/g, `$1${thousands}`) +
      (decimalCount
        ? decimal +
          Math.abs(amount - i)
            .toFixed(decimalCount)
            .slice(2)
        : '')} ${currency}`;
  } catch (e) {
    console.log(e);
  }
}

const overwriteMerge = (destinationArray, sourceArray) => sourceArray;

export function DEEEEEEP(parent_object, child_object_to_add) {
  // update object state data with new data, while keeping untouched old data, overwrite array
  return merge(parent_object, child_object_to_add, {
    arrayMerge: overwriteMerge,
  });
}

export function addCreditTransferIdsToTransferAccount(
  parent_object,
  child_object_to_add,
) {
  // update object state data with new data, while keeping untouched old data, merge arrays
  return merge(parent_object, child_object_to_add);
}

export const generateQueryString = query => {
  let query_string = '?';

  if (query) {
    Object.keys(query).map(query_key => {
      const string_term = `${query_key}=${query[query_key]}&`;
      query_string = query_string.concat(string_term);
    });
  }

  const orgId = getOrgId();
  let response_string = query_string;
  if (orgId !== null && typeof orgId !== 'undefined') {
    response_string = `${query_string}org=${orgId}&`;
  }

  return response_string.slice(0, -1);
};

export const parseQuery = queryString => {
  const query = {};
  const pairs = (queryString[0] === '?'
    ? queryString.substr(1)
    : queryString
  ).split('&');
  for (let i = 0; i < pairs.length; i++) {
    const pair = pairs[i].split('=');
    query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
  }
  return query;
};

export const generateFormattedURL = (url, query, path) => {
  let URL;
  let version = store.getState().login.webApiVersion;
  if (!version) {
    version = '1'; // fallback to V1 API
  }
  const query_string = generateQueryString(query);
  if (url === null || typeof url === 'undefined') {
    return console.log('URL cannot be null');
  }
  if (query) {
    URL = `/api/v${version}${url}${query_string}`;
  } else if (path) {
    URL = `/api/v${version}${url}${path}/${query_string}`;
  } else {
    URL = `/api/v${version}${url}${query_string}`;
  }
  return URL;
};

export const handleResponse = response => {
  if (response.ok) {
    return response.json();
  }
  return Promise.reject(response);
};

export function* handleError(error) {
  const status = error.statusText;

  try {
    const json = yield call(extractJson, error);
    var { message } = json;
  } catch (parse_error) {
    message = 'Something went wrong.';
  }

  if (error.status === 401) {
    yield put({ type: LOGIN_FAILURE, error: message });
  }

  return { message, status };
}

const extractJson = error => error.json();

export const storeOrgid = orgId => {
  localStorage.setItem('orgId', orgId);
};

export const removeOrgId = orgId => {
  localStorage.removeItem('orgId');
};

export const getOrgId = () => {
  try {
    return localStorage.getItem('orgId');
  } catch (err) {
    removeOrgId();
    return null;
  }
};

export const storeSessionToken = token => {
  localStorage.setItem('sessionToken', token);
};

export const removeSessionToken = () => {
  localStorage.removeItem('sessionToken');
};

export const storeTFAToken = token => {
  localStorage.setItem('TFAToken', token);
};

export const removeTFAToken = () => {
  localStorage.removeItem('TFAToken');
};

export const getTFAToken = () => {
  try {
    return localStorage.getItem('TFAToken');
  } catch (err) {
    removeTFAToken();
    return null;
  }
};

export const getToken = () => {
  try {
    const sessionToken = localStorage.getItem('sessionToken');
    const TFAToken = localStorage.getItem('TFAToken');

    if (TFAToken) {
      return `${sessionToken}|${TFAToken}`;
    }

    return sessionToken;
  } catch (err) {
    removeSessionToken();
    return '';
  }
};

export const replaceUnderscores = stringlike => {
  if (stringlike) {
    return stringlike.toString().replace(/_/g, ' ');
  }
  return '';
};

export const replaceSpaces = stringlike => {
  if (stringlike) {
    return stringlike.toString().replace(/ /g, '-');
  }
  return '';
};

export const getDateArray = (start, end) => {
  const arr = new Array();
  const dt = new Date(start);

  while (dt <= end) {
    arr.push(new Date(dt));
    dt.setDate(dt.getDate() + 1);
  }

  return arr;
};

export const get_zero_filled_values = (key, value_array, date_array) => {
  const value_dict = {};

  value_array.map(data => (value_dict[new Date(data.date)] = data[key]));

  const transaction_volume = date_array.map(date => {
    if (value_dict[date] !== undefined) {
      return value_dict[date] / 100;
    }
    return 0;
  });

  return transaction_volume;
};

export const processFiltersForQuery = filters => {
  let encoded_filters = encodeURIComponent('%$user_filters%');
  filters.forEach(filter => {
    if (
      USER_FILTER_TYPE.DISCRETE == filter.type ||
      USER_FILTER_TYPE.BOOLEAN_MAPPING == filter.type
    ) {
      encoded_filters += encodeURIComponent(`,${filter.keyName}%`);
      filter.allowedValues.forEach(value => {
        encoded_filters += encodeURIComponent(`=${value}%`);
      });
    } else {
      encoded_filters += encodeURIComponent(`,${filter.keyName}%`);
      const parsed_filter = `${filter.type + filter.threshold}%`;
      encoded_filters += encodeURIComponent(parsed_filter);
    }
  });
  return encoded_filters;
};
