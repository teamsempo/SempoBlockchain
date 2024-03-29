import { DEEEEEEP } from "../utils";
import {
  APILifecycleActionTypesInterface,
  byIdState,
  IdListState,
  paginationState,
  asyncIdState,
  Registration,
  RequestingState,
} from "./types";
import {
  deepUpdateObjectsActionType,
  replaceIdListActionType,
  replacePaginationActionType,
  replaceUpdateObjectsActionType,
  replaceAsyncIdActionType,
} from "./actions";

export const lifecycleReducerFactory = (
  actionType: APILifecycleActionTypesInterface,
  reg: Registration
): ((state: RequestingState | undefined, action: any) => RequestingState) => {
  const initialLoaderState = {
    isRequesting: false,
    success: false,
    error: null,
  };
  return (
    state: RequestingState | undefined = initialLoaderState,
    action: any
  ): RequestingState => {
    switch (action.type) {
      case actionType.request(reg.name):
        return { ...state, isRequesting: true };

      case actionType.success(reg.name):
        return { ...state, isRequesting: false, success: true };

      case actionType.failure(reg.name):
        return {
          ...state,
          isRequesting: false,
          success: false,
          error: action.error,
        };

      default:
        return state;
    }
  };
};

export const byIdReducerFactory = (
  reg: Registration
): ((state: byIdState | undefined, action: any) => byIdState) => {
  return (state: byIdState | undefined = {}, action: any): byIdState => {
    switch (action.type) {
      case deepUpdateObjectsActionType(reg.name):
        return DEEEEEEP(state, action.objects);

      case replaceUpdateObjectsActionType(reg.name):
        return action.objects;

      default:
        return state;
    }
  };
};

export const idListReducerFactory = (
  reg: Registration
): ((state: IdListState | undefined, action: any) => IdListState) => {
  return (state: IdListState | undefined = [], action: any): IdListState => {
    switch (action.type) {
      case replaceIdListActionType(reg.name):
        return (state = action.idList);
      default:
        return state;
    }
  };
};

export const paginationReducerFactory = (
  reg: Registration
): ((state: paginationState | undefined, action: any) => paginationState) => {
  return (state: paginationState | any, action: any): paginationState => {
    switch (action.type) {
      case replacePaginationActionType(reg.name):
        return (state = action.pagination);
      default:
        return state || {};
    }
  };
};

export const asyncIdReducerFactory = (
  reg: Registration
): ((state: asyncIdState | undefined, action: any) => asyncIdState) => {
  return (state: asyncIdState | any, action: any): asyncIdState => {
    switch (action.type) {
      case replaceAsyncIdActionType(reg.name): {
        return (state = action.asyncId);
      }
      default:
        return state || "";
    }
  };
};
