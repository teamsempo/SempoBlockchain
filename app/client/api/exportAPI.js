import {generateQueryString, getToken, handleResponse} from '../utils'

export const exportAPI = (export_type, include_transfers, user_type, date_range, payable_period_start_date, payable_period_end_date, selected) => {
  const query_string = generateQueryString();
  var URL = `/api/export/${query_string}`;

  return fetch(URL, {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify({
        export_type: export_type,
        include_transfers: include_transfers,
        user_type: user_type,
        date_range: date_range,
        payable_period_start_date: payable_period_start_date,
        payable_period_end_date: payable_period_end_date,
        selected: selected
    })
  }).then(response => {
      return response.json();
    })
    .catch(error => {
      throw error;
    })
};