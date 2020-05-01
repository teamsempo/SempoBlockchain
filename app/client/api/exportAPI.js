import { apiClient } from "./apiClient";

export const exportAPI = ({ body }) =>
  apiClient({
    url: "/export/",
    method: "POST",
    body: body
  });
