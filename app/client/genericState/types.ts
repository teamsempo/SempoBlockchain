import { Schema } from "normalizr";
import { Reducer } from "redux";
import { GetRequest, PostRequest, PutRequest } from "./api";
import { Body } from "../api/client/types";

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

export type paginationState = any;

export type asyncIdState = any;

// The Generics here correspond to the Body sent during either Create or Modify requests.
export interface Registration<CB extends Body = Body, MB extends Body = CB> {
  name: string;
  schema: Schema;
  endpoint?: string;
  singularData?: string;
  pluralData?: string;
  _?: CB | MB; //Prevents a "declared but never used" error
}

export interface EndpointedRegistration<
  CB extends Body = Body,
  MB extends Body = CB
> extends Registration<CB, MB> {
  endpoint: string;
}

export interface RegistrationMapping {
  [key: string]: Registration;
}

export interface EndpointedRegistrationMapping {
  [key: string]: EndpointedRegistration;
}
