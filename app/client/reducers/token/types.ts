export enum TokenListActionTypes {
  UPDATE_TOKEN_LIST = "UPDATE_TOKEN_LIST"
}

export enum LoadTokenActionTypes {
  LOAD_TOKENS_REQUEST = "LOAD_TOKENS_REQUEST",
  LOAD_TOKENS_SUCCESS = "LOAD_TOKENS_SUCCESS",
  LOAD_TOKENS_FAILURE = "LOAD_TOKENS_FAILURE"
}

export enum CreateTokenActionTypes {
  CREATE_TOKEN_REQUEST = "CREATE_TOKEN_REQUEST",
  CREATE_TOKEN_SUCCESS = "CREATE_TOKEN_SUCCESS",
  CREATE_TOKEN_FAILURE = "CREATE_TOKEN_FAILURE",
  RESET_CREATE_TOKEN = "RESET_CREATE_TOKEN"
}

export interface CreateToken {
  token_name: string;
  token_attributes: object;
}

export interface Token {
  address: string;
  symbol: string;
  name: string;
  id: number;
  exchange_rates: object;
  created: string;
  updated: string;
}

export interface CreateTokenPayload {
  body: CreateToken;
}

export interface TokenData {
  tokens: Token[];
  token: Token;
}
