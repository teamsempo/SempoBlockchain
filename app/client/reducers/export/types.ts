export interface ExportPayload {
  body: {
    export_type: string;
    include_transfers: boolean;
    user_type: string;
    date_range: string;
    payable_period_start_date?: string;
    payable_period_end_date?: string;
    selected: [];
  };
}

export interface ExportSuccessPayload {
  file_url?: string;
}

export enum ExportActionTypes {
  NEW_EXPORT_REQUEST = "NEW_EXPORT_REQUEST",
  NEW_EXPORT_SUCCESS = "NEW_EXPORT_SUCCESS",
  NEW_EXPORT_FAILURE = "NEW_EXPORT_FAILURE",
  RESET_EXPORT = "RESET_EXPORT"
}
