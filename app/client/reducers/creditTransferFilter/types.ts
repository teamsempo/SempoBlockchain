export enum CreditTransferFiltersActionTypes {
  LOAD_CREDIT_TRANSFER_FILTERS_REQUEST = "LOAD_CREDIT_TRANSFER_FILTERS_REQUEST",
  LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS = "LOAD_CREDIT_TRANSFER_FILTERS_SUCCESS",
  LOAD_CREDIT_TRANSFER_FILTERS_FAILURE = "LOAD_CREDIT_TRANSFER_FILTERS_FAILURE",
  UPDATE_CREDIT_TRANSFER_FILTERS = "UPDATE_CREDIT_TRANSFER_FILTERS"
}

export interface CreditTransferFilters {
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
