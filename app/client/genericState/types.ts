import { Schema } from "normalizr";
import { Reducer } from "redux";
import { GetRequest, PostRequest, PutRequest } from "../api/genericAPI";

export interface ActionGenerator {
  (name: string): string;
}

export interface APILifecycleActionTypesInterface {
  stage: string;
  request: ActionGenerator;
  success: ActionGenerator;
  failure: ActionGenerator;
}

type NoURL<T> = Pick<T, Exclude<keyof T, "url">>;

interface Action {
  type: string;
}

export type ApiRequest = GetRequest | PostRequest | PutRequest;

export interface LoadRequestAction extends Action {
  payload: NoURL<GetRequest>;
}

export interface CreateRequestAction extends Action {
  payload: NoURL<PostRequest>;
}

export interface ModifyRequestAction extends Action {
  payload: NoURL<PutRequest>;
}

export interface ApiRequestAction extends Action {
  payload: NoURL<ApiRequest>;
}

export interface RequestingState {
  isRequesting: boolean;
  success: boolean;
  error: null | string;
}

export interface Result {
  [key: string]: any;
}

export interface byIdState {
  [key: number]: any;
}

export type IdListState = (number | string)[];

export interface Registration {
  name: string;
  schema: Schema;
  endpoint?: string;
  singularData?: string;
  pluralData?: string;
}

export interface HasEndpointRegistration extends Registration {
  endpoint: string;
}

export interface RegistrationMapping {
  [key: string]: Registration | HasEndpointRegistration;
}

export interface BaseReducerMapping {
  [key: string]: Reducer;
}
