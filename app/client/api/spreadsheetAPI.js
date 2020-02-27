import { apiClient } from "./apiClient";

export const uploadSpreadsheetAPI = ({ body }) =>
  apiClient({
    url: "/spreadsheet/upload/",
    method: "POST",
    isForm: true,
    body: body
  });

export const saveDatasetAPI = ({ body }) =>
  apiClient({ url: "/dataset/", method: "POST", body: body });

export const loadDatasetListAPI = () =>
  apiClient({ url: "/dataset/", method: "GET" });
