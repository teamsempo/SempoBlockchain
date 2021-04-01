import { ExportActionTypes } from "./types";
import { ExportAction } from "./actions";

interface RequestingState {
  isRequesting: boolean;
  success: boolean;
  error: null | string;
  message?: null | string;
}

export const initialExportState: RequestingState = {
  isRequesting: false,
  success: false,
  error: null,
  message: null
};

export const ExportReducer = (
  state = initialExportState,
  action: ExportAction
) => {
  switch (action.type) {
    case ExportActionTypes.RESET_EXPORT:
      return initialExportState;
    case ExportActionTypes.NEW_EXPORT_REQUEST:
      return { ...state, isRequesting: true, error: null, success: false };
    case ExportActionTypes.NEW_EXPORT_SUCCESS:
      return {
        ...state,
        isRequesting: false,
        success: true,
        message: action.payload.message
      };
    case ExportActionTypes.NEW_EXPORT_FAILURE:
      return {
        ...state,
        isRequesting: false,
        error: action.error
      };
    default:
      return state;
  }
};
