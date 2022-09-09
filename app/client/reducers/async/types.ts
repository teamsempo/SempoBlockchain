export interface LoadAsnycPayload {
  query?: {};
  path?: number;
}

export enum LoadAsyncActionType {
  LOAD_ASYNC_REQUEST = "LOAD_ASYNC_REQUEST",
  LOAD_ASYNC_SUCCESS = "LOAD_ASYNC_SUCCESS",
  LOAD_ASYNC_FAILURE = "LOAD_ASYNC_FAILURE",
}

export interface AsyncData {
  message: string;
  percent_complete: number;
}
