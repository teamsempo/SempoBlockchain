import {
  LoadAsyncActionType,
  LoadAsyncPayload,
  AsyncActionType,
} from "./types";
import { ActionsUnion, createAction } from "../../reduxUtils";

export const AsyncAction = {
  updateAsync: (asyncData: any) =>
    createAction(AsyncActionType.UPDATE_ASYNC, asyncData),
  clearAsync: () => createAction(AsyncActionType.UPDATE_ASYNC, {}),
};
export type AsyncAction = ActionsUnion<typeof AsyncAction>;

export const LoadAsyncAction = {
  loadAsyncRequest: (payload: LoadAsyncPayload) =>
    createAction(LoadAsyncActionType.LOAD_ASYNC_REQUEST, payload),
  loadASyncSuccess: () => createAction(LoadAsyncActionType.LOAD_ASYNC_SUCCESS),
  loadAsyncFailure: (error: string) =>
    createAction(LoadAsyncActionType.LOAD_ASYNC_FAILURE, error),
};
export type LoadAsyncAction = ActionsUnion<typeof LoadAsyncAction>;
