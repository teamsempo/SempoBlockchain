export const RESET_EXPORT = 'RESET_EXPORT';
export const NEW_EXPORT_REQUEST = 'NEW_EXPORT_REQUEST';
export const NEW_EXPORT_SUCCESS = 'NEW_EXPORT_SUCCESS';
export const NEW_EXPORT_FAILURE = 'NEW_EXPORT_FAILURE';

export const initialExportState = {
  isRequesting: false,
  success: false,
  error: null,
  file_url: null,
};

export const newExportRequest = (state = initialExportState, action) => {
  switch (action.type) {
    case RESET_EXPORT:
      return initialExportState;
    case NEW_EXPORT_REQUEST:
      return {
        ...state,
        isRequesting: true,
        error: null,
        success: false,
      };
    case NEW_EXPORT_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        success: true,
        file_url: action.result.file_url,
      };
    case NEW_EXPORT_FAILURE:
      return {
        ...state,
        isRequesting: false,
        error: action.error || 'unknown error',
      };
    default:
      return state;
  }
};

// Actions
export const newExport = payload => ({
  type: NEW_EXPORT_REQUEST,
  payload,
});
