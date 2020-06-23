import { SpreadsheetActionTypes } from "./types";
import { SpreadsheetAction } from "./actions";

const initialuploadState = {
  isRequesting: false,
  error: null,
  data: null
};

export const spreadsheetUpload = (
  state = initialuploadState,
  action: SpreadsheetAction
) => {
  switch (action.type) {
    case SpreadsheetActionTypes.RESET_UPLOAD_STATE:
      return initialuploadState;

    case SpreadsheetActionTypes.SPREADSHEET_UPLOAD_REQUEST:
      return { ...state, isRequesting: true };

    case SpreadsheetActionTypes.SPREADSHEET_UPLOAD_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        data: action.payload.upload_result,
        error: null
      };

    case SpreadsheetActionTypes.SPREADSHEET_UPLOAD_FAILURE:
      return {
        ...state,
        isRequesting: false,
        data: null,
        error: action.payload.error || "unknown error"
      };

    default:
      return state;
  }
};

const intialSaveDatasetState = {
  isRequesting: false,
  error: null,
  saved: false,
  message: "",
  diagnostics: []
};

export const datasetSave = (
  state = intialSaveDatasetState,
  action: SpreadsheetAction
) => {
  switch (action.type) {
    case SpreadsheetActionTypes.RESET_UPLOAD_STATE:
      return intialSaveDatasetState;

    case SpreadsheetActionTypes.SAVE_DATASET_REQUEST:
      return { ...state, isRequesting: true, saved: false };

    case SpreadsheetActionTypes.SAVE_DATASET_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        saved: true,
        error: null,
        message: action.payload.save_result.message,
        diagnostics: action.payload.save_result.diagnostics
      };

    case SpreadsheetActionTypes.SAVE_DATASET_FAILURE:
      return {
        ...state,
        isRequesting: false,
        saved: false,
        error: action.payload.error || "unknown error"
      };

    default:
      return state;
  }
};

const intialDatasetListState = {
  isRequesting: false,
  error: null,
  data: {}
};

export const datasetList = (
  state = intialDatasetListState,
  action: SpreadsheetAction
) => {
  switch (action.type) {
    case SpreadsheetActionTypes.LOAD_DATASET_LIST_REQUEST:
      return { ...state, isRequesting: true };

    case SpreadsheetActionTypes.LOAD_DATASET_LIST_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        error: null,
        data: { ...state.data, ...action.payload.load_result.data }
      };

    case SpreadsheetActionTypes.LOAD_DATASET_LIST_FAILURE:
      return {
        ...state,
        isRequesting: false,
        error: action.payload.error || "unknown error"
      };

    default:
      return state;
  }
};
