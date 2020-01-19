export const RESET_UPLOAD_STATE = "RESET_UPLOAD_STATE";

export const SPREADSHEET_UPLOAD_REQUEST = "SPREADSHEET_UPLOAD_REQUEST";
export const SPREADSHEET_UPLOAD_SUCCESS = "SPREADSHEET_UPLOAD_SUCCESS";
export const SPREADSHEET_UPLOAD_FAILURE = "SPREADSHEET_UPLOAD_FAILURE";

export const SAVE_DATASET_REQUEST = "SAVE_DATASET_REQUEST";
export const SAVE_DATASET_SUCCESS = "SAVE_DATASET_SUCCESS";
export const SAVE_DATASET_FAILURE = "SAVE_DATASET_FAILURE";

export const LOAD_DATASET_LIST_REQUEST = "LOAD_DATASET_LIST_REQUEST";
export const LOAD_DATASET_LIST_SUCCESS = "LOAD_DATASET_LIST_SUCCESS";
export const LOAD_DATASET_LIST_FAILURE = "LOAD_DATASET_LIST_FAILURE";

const initialuploadState = {
  isRequesting: false,
  error: null,
  data: null
};

export const spreadsheetUpload = (state = initialuploadState, action) => {
  switch (action.type) {

    case RESET_UPLOAD_STATE:
      return initialuploadState

    case SPREADSHEET_UPLOAD_REQUEST:
      return {...state, isRequesting: true};

    case SPREADSHEET_UPLOAD_SUCCESS:
      return {...state, isRequesting: false, data: action.upload_result, error: null};

    case SPREADSHEET_UPLOAD_FAILURE:
      return {...state, isRequesting: false, data: null, error: action.error || 'unknown error'};

    default:
      return state;
  }
};

const intialSaveDatasetState = {
  isRequesting: false,
  error: null,
  saved: false,
  message: '',
  diagnostics: [],
};

export const datasetSave = (state = intialSaveDatasetState, action) => {
  switch (action.type) {

    case RESET_UPLOAD_STATE:
      return intialSaveDatasetState;

    case SAVE_DATASET_REQUEST:
      return {...state, isRequesting: true, saved: false};

    case SAVE_DATASET_SUCCESS:
      return {...state, isRequesting: false, saved: true, error: null, message: action.save_result.message, diagnostics: action.save_result.diagnostics};

    case SAVE_DATASET_FAILURE:
      return {...state, isRequesting: false, saved: false, error: action.error || 'unknown error'};

    default:
      return state;
  }
};

const intialDatasetListState = {
  isRequesting: false,
  error: null,
  data: {}
};

export const datasetList = (state = intialDatasetListState, action) => {
  switch (action.type) {

    case LOAD_DATASET_LIST_REQUEST:
      return {...state, isRequesting: true};

    case LOAD_DATASET_LIST_SUCCESS:
      return {...state, isRequesting: false, error: null, data: {...state.data, ...action.load_result.data}};

    case LOAD_DATASET_LIST_FAILURE:
      return {...state, isRequesting: false, error: action.error || 'unknown error'};

    default:
      return state;
  }
};

/// Actions

export const uploadSpreadsheet = (spreadsheet, preview_id, transfer_account_type) => (
  {
    type: SPREADSHEET_UPLOAD_REQUEST,
    spreadsheet,
    preview_id,
    transfer_account_type
  }
);

export const saveDataset = (payload) => (
  {
    type: SAVE_DATASET_REQUEST,
    payload
  }
);

export const resetUploadState = () => (
  {
  type: RESET_UPLOAD_STATE
  }
);

export const loadDatasetList = () => (
  {
    type: LOAD_DATASET_LIST_REQUEST,
    datasetList
  }
);

