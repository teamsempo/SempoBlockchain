import { WyreActionTypes, WyreState } from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const loadExchangeRatesRequest = (payload: any) =>
  createAction(WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_REQUEST, payload);

export const loadExchangeRatesSuccess = () =>
  createAction(WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_SUCCESS);

export const loadExchangeRatesFailure = (error: any) =>
  createAction(WyreActionTypes.LOAD_WYRE_EXCHANGE_RATES_FAILURE, { error });

export const loadWyreAccountRequest = () =>
  createAction(WyreActionTypes.LOAD_WYRE_ACCOUNT_REQUEST);

export const loadWyreAccountSuccess = () =>
  createAction(WyreActionTypes.LOAD_WYRE_ACCOUNT_SUCCESS);

export const loadWyreAccountFailure = (error: any) =>
  createAction(WyreActionTypes.LOAD_WYRE_ACCOUNT_FAILURE, { error });

export const createWyreTransferRequest = (payload: any) =>
  createAction(WyreActionTypes.CREATE_WYRE_TRANSFER_REQUEST, payload);

export const createWyreTransferSuccess = () =>
  createAction(WyreActionTypes.CREATE_WYRE_TRANSFER_SUCCESS);

export const createWyreTransferFailure = (error: any) =>
  createAction(WyreActionTypes.CREATE_WYRE_TRANSFER_FAILURE, { error });

export const updateWyreState = (payload: WyreState) =>
  createAction(WyreActionTypes.UPDATE_WYRE_STATE, payload);

export const WyreAction = {
  loadExchangeRatesRequest,
  loadExchangeRatesSuccess,
  loadExchangeRatesFailure,
  loadWyreAccountRequest,
  loadWyreAccountSuccess,
  loadWyreAccountFailure,
  createWyreTransferRequest,
  createWyreTransferSuccess,
  createWyreTransferFailure,
  updateWyreState
};

export type WyreAction = ActionsUnion<typeof WyreAction>;
