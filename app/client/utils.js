import { call, put } from "redux-saga/effects";
import merge from "deepmerge";
import { LoginAction } from "./reducers/auth/actions";
import store from "./createStore.js";
import { USER_FILTER_TYPE } from "./constants";
import { allowedFilters } from "./reducers/allowedFilters/reducers";

export function formatMoney(
  amount,
  decimalCount,
  decimal = ".",
  thousands = ",",
  currency
) {
  try {
    decimalCount = Math.abs(decimalCount);
    decimalCount = isNaN(decimalCount) ? 2 : decimalCount;

    const negativeSign = amount < 0 ? "-" : "";

    let i = parseInt(
      (amount = Math.abs(Number(amount) || 0).toFixed(decimalCount))
    ).toString();
    let j = i.length > 3 ? i.length % 3 : 0;

    return (
      negativeSign +
      (j ? i.substr(0, j) + thousands : "") +
      i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thousands) +
      (decimalCount
        ? decimal +
          Math.abs(amount - i)
            .toFixed(decimalCount)
            .slice(2)
        : "") +
      (currency ? " " + currency : "")
    );
  } catch (e) {
    console.log(e);
  }
}

export const toCurrency = amount => {
  return Math.round((amount / 100) * 100) / 100;
};

const overwriteMerge = (destinationArray, sourceArray) => sourceArray;

export function DEEEEEEP(parent_object, child_object_to_add) {
  // update object state data with new data, while keeping untouched old data, overwrite array
  return merge(parent_object, child_object_to_add, {
    arrayMerge: overwriteMerge
  });
}

export function addCreditTransferIdsToTransferAccount(
  parent_object,
  child_object_to_add
) {
  // update object state data with new data, while keeping untouched old data, merge arrays
  return merge(parent_object, child_object_to_add);
}

export const generateQueryString = query => {
  let query_string = "?";

  if (query) {
    Object.keys(query).map(query_key => {
      let string_term = query_key + "=" + query[query_key] + "&";
      if (!/^\s*$/.test(query[query_key])) {
        // We don't want to include empty string keys ' ', i.e. ?params=
        query_string = query_string.concat(string_term);
      }
    });
  }

  let orgId = getOrgId();
  var response_string = query_string;
  if (orgId !== null && typeof orgId !== "undefined") {
    response_string = query_string + `org=${orgId}&`;
  }

  return response_string.slice(0, -1);
};

export const parseQuery = queryString => {
  var query = {};
  var pairs = (queryString[0] === "?"
    ? queryString.substr(1)
    : queryString
  ).split("&");
  for (var i = 0; i < pairs.length; i++) {
    var pair = pairs[i].split("=");
    query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || "");
  }
  if (
    Object.keys(query).filter(key => {
      if (/^\s*$/.test(key) || /^\s*$/.test(query[key])) {
        // delete empty string key value pairs, e.g. {"":""}
        delete query[key];
      }
    })
  )
    return query;
};

export const generateFormattedURLPath = (url, query, path) => {
  let urlPath;
  let version;

  try {
    version = store.getState().login.webApiVersion;
  } catch (e) {
    console.log("Something went wrong", e);
    version = null;
  }

  if (!version) {
    version = "1"; // fallback to V1 API
  }
  let query_string = generateQueryString(query);
  if (url === null || typeof url === "undefined") {
    return console.log("URL cannot be null");
  } else if (query) {
    urlPath = `/api/v${version}${url}${query_string}`;
  } else if (path) {
    urlPath = `/api/v${version}${url}${path}/${query_string}`;
  } else {
    urlPath = `/api/v${version}${url}${query_string}`;
  }
  return urlPath;
};

export const generateFormattedURL = (url, query, path) => {
  let urlPath = generateFormattedURLPath(url, query, path);
  const baseUrl = window && window.location ? `${window.location.origin}` : "";
  return new URL(urlPath, baseUrl).href;
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
    var message = json.message;
  } catch (parse_error) {
    message = "Something went wrong.";
  }

  if (error.status === 401) {
    yield put(LoginAction.loginFailure(message));
  }

  return { message, status };
}

const extractJson = error => {
  return error.json();
};

export const storeOrgid = orgId => {
  localStorage.setItem("orgId", orgId);
};

export const removeOrgId = orgId => {
  localStorage.removeItem("orgId");
};

export const getOrgId = () => {
  try {
    return localStorage.getItem("orgId");
  } catch (err) {
    removeOrgId();
    return null;
  }
};

export const storeSessionToken = token => {
  localStorage.setItem("sessionToken", token);
};

export const removeSessionToken = () => {
  localStorage.removeItem("sessionToken");
};

export const storeTFAToken = token => {
  localStorage.setItem("TFAToken", token);
};

export const removeTFAToken = () => {
  localStorage.removeItem("TFAToken");
};

export const getTFAToken = () => {
  try {
    return localStorage.getItem("TFAToken");
  } catch (err) {
    removeTFAToken();
    return null;
  }
};

export const getToken = () => {
  try {
    let sessionToken = localStorage.getItem("sessionToken");
    let TFAToken = localStorage.getItem("TFAToken");

    if (TFAToken) {
      return sessionToken + "|" + TFAToken;
    }

    return sessionToken;
  } catch (err) {
    removeSessionToken();
    return "";
  }
};

export const replaceUnderscores = stringlike => {
  if (stringlike) {
    return stringlike.toString().replace(/_/g, " ");
  } else {
    return "";
  }
};

export const toTitleCase = stringlike => {
  if (stringlike) {
    return stringlike.replace(/\w\S*/g, function(txt) {
      return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
  } else {
    return "";
  }
};

export const replaceSpaces = stringlike => {
  if (stringlike) {
    return stringlike.toString().replace(/ /g, "-");
  } else {
    return "";
  }
};

export const getDateArray = (start, end) => {
  var arr = new Array(),
    dt = new Date(start);

  while (dt <= end) {
    arr.push(new Date(dt));
    dt.setDate(dt.getDate() + 1);
  }

  return arr;
};

export const get_zero_filled_values = (key, value_array, date_array) => {
  let value_dict = {};

  value_array.map(data => (value_dict[new Date(data.date)] = data[key]));

  let transaction_volume = date_array.map(date => {
    if (value_dict[date] !== undefined) {
      return value_dict[date];
    } else {
      return 0;
    }
  });

  return transaction_volume;
};

export const processFiltersForQuery = filters => {
  let encoded_filters = encodeURIComponent("");
  let delimiter = ":";
  // let encoded_filters = encodeURIComponent("%$user_filters%");

  filters.forEach(filter => {
    encoded_filters += encodeURIComponent(filter.attribute);
    let parsed_filter = "";
    if (
      USER_FILTER_TYPE.DISCRETE === filter.type ||
      USER_FILTER_TYPE.BOOLEAN_MAPPING === filter.type
    ) {
      let rule = "(IN)";
      let allowed_vals = "";
      filter.allowedValues.forEach(value => {
        allowed_vals += encodeURIComponent(value) + ",";
      });

      parsed_filter = `${rule}(${allowed_vals.slice(0, -1)})`;
    } else {
      let rule = "";
      if (filter.type === ">") {
        rule = "(GT)";
      } else if (filter.type === "<") {
        rule = "(LT)";
      } else {
        rule = "(EQ)";
      }
      let threshold = `(${encodeURIComponent(filter.threshold)})`;

      parsed_filter = rule + threshold;
    }

    encoded_filters += parsed_filter + delimiter;
  });

  encoded_filters = encoded_filters.slice(0, -delimiter.length);

  return encoded_filters;
};

export const parseEncodedParams = (allowedFilters, params) => {
  let filters = [];
  let param_array;
  let allowedValues;
  let gt;
  let lt;
  let eq;
  try {
    if (allowedFilters && params) {
      param_array = params.split(":");
      param_array.map((param, i) => {
        let filter = {};
        let filterAttribute = param.split("(")[0];
        filter["type"] = allowedFilters[filterAttribute].type;
        if (
          USER_FILTER_TYPE.DISCRETE === filter.type ||
          USER_FILTER_TYPE.BOOLEAN_MAPPING === filter.type
        ) {
          allowedValues = param.split("(IN)")[1];
          filter["allowedValues"] = allowedValues
            .substr(1, allowedValues.length - 2)
            .split(",");
          filter["attribute"] = filterAttribute;
          filter["id"] = i + 1;
        } else {
          gt = param.split("(GT)");
          lt = param.split("(LT)");
          eq = param.split("(EQ)");
          if (gt.length > 1) {
            allowedValues = gt[1];
            filter["type"] = ">";
            filter["threshold"] = allowedValues.substr(
              1,
              allowedValues.length - 2
            );
          } else if (lt.length > 1) {
            allowedValues = lt[1];
            filter["type"] = "<";
            filter["threshold"] = allowedValues.substr(
              1,
              allowedValues.length - 2
            );
          } else {
            allowedValues = eq[1];
            filter["type"] = "=";
            filter["threshold"] = allowedValues.substr(
              1,
              allowedValues.length - 2
            );
          }
          filter["attribute"] = filterAttribute;
          filter["id"] = i + 1;
        }

        filters.push(filter);
      });
    }
  } catch (e) {
    console.log("Something went wrong", e);
    allowedFilters = null;
  }
  return filters;
};

export const flattenObject = obj => {
  // Input = {group_key1: {queryKey1: queryValue1}, group_key2: {queryKey2: queryValue2} ...}
  // Output = {group_key1.queryKey1: queryValue1, group_key2.queryKey2: queryValue2 ...}
  let new_obj = {};
  Object.keys(obj).map(group_key => {
    Object.keys(obj[group_key]).map(key => {
      new_obj[group_key + "." + key] = obj[group_key][key];
    });
  });
  return new_obj;
};

export const expandObject = obj => {
  // Input = {group_key1.queryKey1: queryValue1, group_key2.group_key2: queryValue2 ...}
  // Output = {group_key1: {queryKey1: queryValue1}, group_key2: {queryKey2: queryValue2} ...}
  let new_obj = {};
  Object.keys(obj).map(key => {
    let group_key = key.split(".")[0];
    let individual_key = key.split(".")[1];
    if (!new_obj.hasOwnProperty(group_key)) {
      new_obj[group_key] = {};
    }
    new_obj[group_key][individual_key] = obj[key];
  });
  return new_obj;
};

export const inverseFilterObject = (obj, filterKey) => {
  let new_obj = {};
  Object.keys(obj)
    .filter(key => {
      if (!key.includes(filterKey)) {
        return key;
      }
    })
    .map(key => (new_obj[key] = obj[key]));
  return new_obj;
};

export const generateGroupQueryString = query_set => {
  query_set = flattenObject(query_set);
  return generateQueryString(query_set);
};

export const parseQueryStringToFilterObject = search => {
  let existingQuery = parseQuery(search);

  let expandedQuery = null;
  if (existingQuery && !/^\s*$/.test(existingQuery)) {
    expandedQuery = expandObject(existingQuery);
  }

  return expandedQuery;
};

export function hexToRgb(hex) {
  // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
  var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
  hex = hex.replace(shorthandRegex, function(m, r, g, b) {
    return r + r + g + g + b + b;
  });

  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      }
    : null;
}
