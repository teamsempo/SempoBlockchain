import { apiClient } from "./client/apiClient";
import { CreateTokenPayload } from "../reducers/token/types";

export const loadSavedTokens = () =>
  apiClient({ url: "/token/", method: "GET" });

export const createTokenAPI = ({ body }: CreateTokenPayload) =>
  apiClient({ url: "/token/", method: "POST", body: body });
