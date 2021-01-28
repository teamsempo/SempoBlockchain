import {
  LoadTokenActionTypes,
  TokenListActionTypes,
  CreateTokenActionTypes,
  CreateTokenPayload,
  Token
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const TokenListAction = {
  updateTokenList: (tokens: Token[]) =>
    createAction(TokenListActionTypes.UPDATE_TOKEN_LIST, tokens)
};
export type TokenListAction = ActionsUnion<typeof TokenListAction>;

export const LoadTokenAction = {
  loadTokenRequest: () =>
    createAction(LoadTokenActionTypes.LOAD_TOKENS_REQUEST),
  loadTokenSuccess: () =>
    createAction(LoadTokenActionTypes.LOAD_TOKENS_SUCCESS),
  loadTokenFailure: (error: string) =>
    createAction(LoadTokenActionTypes.LOAD_TOKENS_FAILURE, error)
};
export type LoadTokenAction = ActionsUnion<typeof LoadTokenAction>;

export const CreateTokenAction = {
  createTokenRequest: (payload: CreateTokenPayload) =>
    createAction(CreateTokenActionTypes.CREATE_TOKEN_REQUEST, payload),
  createTokenSuccess: () =>
    createAction(CreateTokenActionTypes.CREATE_TOKEN_SUCCESS),
  createTokenFailure: (error: string) =>
    createAction(CreateTokenActionTypes.CREATE_TOKEN_FAILURE, error),
  createTokenReset: () =>
    createAction(CreateTokenActionTypes.RESET_CREATE_TOKEN)
};
export type CreateTokenAction = ActionsUnion<typeof CreateTokenAction>;
