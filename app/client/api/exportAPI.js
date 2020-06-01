import { apiClient } from "./client/apiClient";

export const exportAPI = ({ body }) =>
  apiClient({
    url: "/export/",
    method: "POST",
    body: body
  });
