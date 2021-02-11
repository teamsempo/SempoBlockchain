import { Body, Query } from "../api/client/types";
import {
  ActionGenerator,
  APILifecycleActionTypesInterface,
  CreateRequestAction,
  LoadRequestAction,
  ModifyRequestAction,
  Registration
} from "./types";

class APILifeCycleActionType implements APILifecycleActionTypesInterface {
  constructor(stage: string) {
    this.stage = stage;
  }

  stage: string;
  request = (name: string) => `${this.stage}_${name}_REQUEST`;
  success = (name: string) => `${this.stage}_${name}_SUCCESS`;
  failure = (name: string) => `${this.stage}_${name}_FAILURE`;
}

export const loadActionTypes = new APILifeCycleActionType("LOAD");
export const createActionTypes = new APILifeCycleActionType("CREATE");
export const modifyActionTypes = new APILifeCycleActionType("MODIFY");

export const deepUpdateObjectsActionType: ActionGenerator = name =>
  `DEEP_UPDATE_${name}`;
export const replaceUpdateObjectsActionType: ActionGenerator = name =>
  `REPLACE_UPDATE_${name}`;
export const replaceIDListActionType: ActionGenerator = name =>
  `REPLACE_${name}_ID_LIST`;

export const actionFactory = {
  load: (
    reg: Registration,
    path?: number,
    query?: Query
  ): LoadRequestAction => ({
    type: loadActionTypes.request(reg.name),
    payload: { path, query }
  }),

  create: (
    reg: Registration,
    query?: Query,
    body?: Body
  ): CreateRequestAction => ({
    type: createActionTypes.request(reg.name),
    payload: { query, body }
  }),

  modify: (
    reg: Registration,
    path?: number,
    query?: Query,
    body?: Body
  ): ModifyRequestAction => ({
    type: createActionTypes.request(reg.name),
    payload: { path, query, body }
  })
};
