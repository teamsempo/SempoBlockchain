export enum FilterListActionTypes {
  UPDATE_FILTER_LIST = "UPDATE_FILTER_LIST"
}

export enum LoadFilterActionTypes {
  LOAD_FILTERS_REQUEST = "LOAD_FILTERS_REQUEST",
  LOAD_FILTERS_SUCCESS = "LOAD_FILTERS_SUCCESS",
  LOAD_FILTERS_FAILURE = "LOAD_FILTERS_FAILURE"
}

export enum CreateFilterActionTypes {
  CREATE_FILTER_REQUEST = "CREATE_FILTER_REQUEST",
  CREATE_FILTER_SUCCESS = "CREATE_FILTER_SUCCESS",
  CREATE_FILTER_FAILURE = "CREATE_FILTER_FAILURE",
  RESET_CREATE_FILTER = "RESET_CREATE_FILTER"
}

export interface CreateFilter {
  filter_name: string;
  filter_attributes: object;
}

export interface Filter {
  name: string;
  filter: object;
}

export interface CreateFilterPayload {
  body: CreateFilter;
}
