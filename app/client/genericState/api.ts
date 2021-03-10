import { apiClient } from "../api/client/apiClient";
import { ApiClientType } from "../api/client/types";

export type GetRequest = Pick<ApiClientType, "url" | "query" | "path">;
export type PutRequest = Pick<ApiClientType, "url" | "query" | "path" | "body">;
export type PostRequest = Pick<ApiClientType, "url" | "query" | "body">;
export const genericGetAPI = ({ url, query, path }: GetRequest) =>
  apiClient({
    method: "GET",
    url: `/${url}/`,
    query: query,
    path: path
  });
export const genericPutAPI = ({ url, query, path, body }: PutRequest) =>
  apiClient({
    method: "PUT",
    url: `/${url}/`,
    query: query,
    path: path,
    body: body
  });
export const genericPostAPI = ({ url, query, body }: PostRequest) =>
  apiClient({
    method: "POST",
    url: `/${url}/`,
    query: query,
    body: body
  });
