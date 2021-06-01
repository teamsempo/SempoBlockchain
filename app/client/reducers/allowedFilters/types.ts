export enum AllowedFiltersActionTypes {
  LOAD_ALLOWED_FILTERS_REQUEST = "LOAD_ALLOWED_FILTERS_REQUEST",
  LOAD_ALLOWED_FILTERS_SUCCESS = "LOAD_ALLOWED_FILTERS_SUCCESS",
  LOAD_ALLOWED_FILTERS_FAILURE = "LOAD_ALLOWED_FILTERS_FAILURE",
  UPDATE_ALLOWED_FILTERS = "UPDATE_ALLOWED_FILTERS"
}

export interface AllowedFilters {
  created: {
    name: string;
    table: string;
    type: string;
  };
  user_type: {
    name: string;
    table: string;
    type: string;
    values: [string];
  };
  gender: {
    name: string;
    table: string;
    type: string;
    values: [string];
  };
  rounded_account_balance: {
    name: string;
    table: string;
    type: string;
  };
}
