import {
  SpreadsheetActionTypes,
  SaveDatasetPayload,
  SpreadsheetUploadPayload,
  SaveDatasetSuccessPayload,
  SpreadsheetUploadSuccessPayload
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const uploadSpreadsheetRequest = (payload: SpreadsheetUploadPayload) =>
  createAction(SpreadsheetActionTypes.SPREADSHEET_UPLOAD_REQUEST, payload);

export const uploadSpreadsheetSuccess = (
  upload_result: SpreadsheetUploadSuccessPayload
) =>
  createAction(SpreadsheetActionTypes.SPREADSHEET_UPLOAD_SUCCESS, {
    upload_result
  });

export const uploadSpreadsheetFailure = (error: any) =>
  createAction(SpreadsheetActionTypes.SPREADSHEET_UPLOAD_FAILURE, { error });

export const saveDatasetRequest = (payload: SaveDatasetPayload) =>
  createAction(SpreadsheetActionTypes.SAVE_DATASET_REQUEST, payload);

export const saveDatasetSuccess = (save_result: SaveDatasetSuccessPayload) =>
  createAction(SpreadsheetActionTypes.SAVE_DATASET_SUCCESS, { save_result });

export const saveDatasetFailure = (error: any) =>
  createAction(SpreadsheetActionTypes.SAVE_DATASET_FAILURE, { error });

export const resetUploadState = () =>
  createAction(SpreadsheetActionTypes.RESET_UPLOAD_STATE);

export const loadDatasetListRequest = (datasetList: any) =>
  createAction(SpreadsheetActionTypes.LOAD_DATASET_LIST_REQUEST, {
    datasetList
  });

export const loadDatasetListSuccess = (load_result: any) =>
  createAction(SpreadsheetActionTypes.LOAD_DATASET_LIST_SUCCESS, {
    load_result
  });

export const loadDatasetListFailure = (error: any) =>
  createAction(SpreadsheetActionTypes.LOAD_DATASET_LIST_FAILURE, { error });

export const SpreadsheetAction = {
  uploadSpreadsheetRequest,
  uploadSpreadsheetSuccess,
  uploadSpreadsheetFailure,
  saveDatasetRequest,
  saveDatasetSuccess,
  saveDatasetFailure,
  resetUploadState,
  loadDatasetListRequest,
  loadDatasetListSuccess,
  loadDatasetListFailure
};

export type SpreadsheetAction = ActionsUnion<typeof SpreadsheetAction>;
