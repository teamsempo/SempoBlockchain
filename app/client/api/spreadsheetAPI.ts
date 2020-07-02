import { apiClient } from "./client/apiClient";
import {
  SaveDatasetPayload,
  SpreadsheetUploadPayload
} from "../reducers/spreadsheet/types";

export const uploadSpreadsheetAPI = ({ body }: SpreadsheetUploadPayload) =>
  apiClient({
    url: "/spreadsheet/upload/",
    method: "POST",
    isForm: true,
    body: body
  });

export const saveDatasetAPI = ({ body }: SaveDatasetPayload) =>
  apiClient({ url: "/dataset/", method: "POST", body: body });

export const loadDatasetListAPI = () =>
  apiClient({ url: "/dataset/", method: "GET" });
