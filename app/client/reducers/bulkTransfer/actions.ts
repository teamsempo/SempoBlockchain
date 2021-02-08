import { createAction, ActionsUnion } from "../../reduxUtils";
import {
  BulkTransferActionTypes,
  BulkTransfersById,
  CreateBulkTransferActionTypes,
  CreateBulkTransferPayload,
  LoadBulkTransfersActionTypes
} from "./types";

export const BulkTransferListAction = {
  deepUpdateBulkTransfers: (bulkTransfers: BulkTransfersById) =>
    createAction(
      BulkTransferActionTypes.DEEP_UPDATE_BULK_TRANSFERS,
      bulkTransfers
    )
};
export type BulkTransferListAction = ActionsUnion<
  typeof BulkTransferListAction
>;

export const LoadBulkTransfersAction = {
  loadBulkTransfersRequest: (payload: CreateBulkTransferPayload) =>
    createAction(
      LoadBulkTransfersActionTypes.LOAD_BULK_TRANSFERS_REQUEST,
      payload
    ),
  loadBulkTransfersSuccess: () =>
    createAction(LoadBulkTransfersActionTypes.LOAD_BULK_TRANSFERS_SUCCESS),
  loadBulkTransfersFailure: (err: string) =>
    createAction(LoadBulkTransfersActionTypes.LOAD_BULK_TRANSFERS_FAILURE, err)
};

export type LoadBulkTransfersAction = ActionsUnion<
  typeof LoadBulkTransfersAction
>;

export const CreateBulkTransferAction = {
  createBulkTransferRequest: (payload: CreateBulkTransferPayload) =>
    createAction(
      CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_REQUEST,
      payload
    ),
  createBulkTransferSuccess: () =>
    createAction(CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_SUCCESS),
  createBulkTransferFailure: (err: string) =>
    createAction(
      CreateBulkTransferActionTypes.CREATE_BULK_TRANSFER_FAILURE,
      err
    )
};

export type CreateBulkTransferAction = ActionsUnion<
  typeof CreateBulkTransferAction
>;
