import { SpreadsheetActionTypes } from "./types";
import { SpreadsheetAction } from "./actions";

interface InitialStateType {
  isRequesting: boolean;
  error?: Error | null;
  data: object | null;
}

const initialState: InitialStateType = {
  isRequesting: false,
  error: null,
  data: null
};

export const spreadsheetUpload = (
  state = initialState,
  action: SpreadsheetAction
) => {
  switch (action.type) {
    case SpreadsheetActionTypes.RESET_UPLOAD_STATE:
      return initialState;

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

interface SaveDatasetState {
  isRequesting: boolean;
  error?: Error | null;
  saved?: boolean;
  message?: string;
}

const intialSaveDatasetState: SaveDatasetState = {
  isRequesting: false,
  error: null,
  saved: false,
  message: ""
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
        message: action.payload.save_result.message
        //diagnostics: action.payload.save_result.diagnostics
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

export const datasetList = (
  state = initialState,
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
