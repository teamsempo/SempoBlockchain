import { Body, Query } from "../api/client/types";
import {
  ActionGenerator,
  APILifecycleActionTypesInterface,
  CreateRequestAction,
  LoadRequestAction,
  ModifyRequestAction,
  Registration,
} from "./types";

class APILifeCycleActionType implements APILifecycleActionTypesInterface {
  constructor(stage: string) {
    this.stage = stage;
  }

  stage: string;
  request = (name: string) => `${this.stage}_${name.toUpperCase()}_REQUEST`;
  success = (name: string) => `${this.stage}_${name.toUpperCase()}_SUCCESS`;
  failure = (name: string) => `${this.stage}_${name.toUpperCase()}_FAILURE`;
}

export const loadActionTypes = new APILifeCycleActionType("LOAD");
export const createActionTypes = new APILifeCycleActionType("CREATE");
export const modifyActionTypes = new APILifeCycleActionType("MODIFY");

export const deepUpdateObjectsActionType: ActionGenerator = (name) =>
  `DEEP_UPDATE_${name.toUpperCase()}`;
export const replaceUpdateObjectsActionType: ActionGenerator = (name) =>
  `REPLACE_UPDATE_${name.toUpperCase()}`;
export const replaceIdListActionType: ActionGenerator = (name) =>
  `REPLACE_${name.toUpperCase()}_ID_LIST`;
export const replacePaginationActionType: ActionGenerator = (name) =>
  `REPLACE_${name.toUpperCase()}_PAGINATION`;

// These functions are designed to be called directly from inside a dispatch,
// and they will return an appropriately shaped action for the given Rest API... action? (load, create, modify)
export const apiActions = {
  load: function <CB, MB>(
    reg: Registration<CB, MB>,
    path?: number,
    query?: Query
  ): LoadRequestAction {
    return {
      type: loadActionTypes.request(reg.name),
      payload: { path, query },
    };
  },

  create: function <CB, MB>(
    reg: Registration<CB, MB>,
    body?: CB,
    query?: Query
  ): CreateRequestAction {
    return {
      type: createActionTypes.request(reg.name),
      payload: { query, body },
    };
  },

  modify: function <CB, MB>(
    reg: Registration<CB, MB>,
    path: number,
    body?: MB,
    query?: Query
  ): ModifyRequestAction {
    return {
      type: modifyActionTypes.request(reg.name),
      payload: { path, query, body },
    };
  },
};
