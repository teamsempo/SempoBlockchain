export interface TransferUsage {
  id: string;
  name: string;
}
export const UPDATE_TRANSFER_USAGES = "UPDATE_TRANSFER_USAGES";
interface UpdateTransferUsages {
  type: typeof UPDATE_TRANSFER_USAGES;
  transferUsages: TransferUsage[];
}
export type TransferUsagesAction = UpdateTransferUsages;

export const LOAD_TRANSFER_USAGES_REQUEST = "LOAD_TRANSFER_USAGES_REQUEST";
interface LoadTransferUsagesRequest {
  type: typeof LOAD_TRANSFER_USAGES_REQUEST;
}
export const LOAD_TRANSFER_USAGES_SUCCESS = "LOAD_TRANSFER_USAGES_SUCCESS";
interface LoadTransferUsagesSuccess {
  type: typeof LOAD_TRANSFER_USAGES_SUCCESS;
}
export const LOAD_TRANSFER_USAGES_FAILURE = "LOAD_TRANSFER_USAGES_FAILURE";
interface LoadTransferUsagesFailure {
  type: typeof LOAD_TRANSFER_USAGES_FAILURE;
  error: string;
}
export type LoadTransferUsagesAction =
  | LoadTransferUsagesRequest
  | LoadTransferUsagesSuccess
  | LoadTransferUsagesFailure;
