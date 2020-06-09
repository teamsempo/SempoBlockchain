import { apiClient } from "./client/apiClient";
import { ExportPayload } from "../reducers/export/types";

export const exportAPI = ({ body }: ExportPayload) =>
  apiClient({
    url: "/export/",
    method: "POST",
    body: body
  });
