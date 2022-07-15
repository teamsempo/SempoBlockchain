export enum SpreadsheetActionTypes {
  RESET_UPLOAD_STATE = "RESET_UPLOAD_STATE",

  SPREADSHEET_UPLOAD_REQUEST = "SPREADSHEET_UPLOAD_REQUEST",
  SPREADSHEET_UPLOAD_SUCCESS = "SPREADSHEET_UPLOAD_SUCCESS",
  SPREADSHEET_UPLOAD_FAILURE = "SPREADSHEET_UPLOAD_FAILURE",

  SAVE_DATASET_REQUEST = "SAVE_DATASET_REQUEST",
  SAVE_DATASET_SUCCESS = "SAVE_DATASET_SUCCESS",
  SAVE_DATASET_FAILURE = "SAVE_DATASET_FAILURE",

  LOAD_DATASET_LIST_REQUEST = "LOAD_DATASET_LIST_REQUEST",
  LOAD_DATASET_LIST_SUCCESS = "LOAD_DATASET_LIST_SUCCESS",
  LOAD_DATASET_LIST_FAILURE = "LOAD_DATASET_LIST_FAILURE",
}

export interface SaveDatasetSuccessPayload {
  message: string;
  status?: string;
}

export interface SaveDatasetPayload {
  body: {
    country: string;
    data: object;
    headerPositions: object;
    customAttributes: object;
    saveName: string;
  };
}

export interface SaveDatasetAPIRequest {
  type: typeof SpreadsheetActionTypes.SAVE_DATASET_REQUEST;
  payload: SaveDatasetPayload;
}

export interface SpreadsheetUploadSuccessPayload {
  column_firstrows?: object;
  requested_attributes?: object;
  table_data?: object;
}

export interface SpreadsheetUploadPayload {
  body: {
    preview_id: number;
    spreadsheet: File;
  };
}

export interface SpreadsheetUploadAPIRequest {
  type: typeof SpreadsheetActionTypes.SPREADSHEET_UPLOAD_REQUEST;
  payload: SpreadsheetUploadPayload;
}
