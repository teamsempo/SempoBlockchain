export interface TransferUsage {
  id: string;
  name: string;
}

export enum TransferUsageActionTypes {
  UPDATE_TRANSFER_USAGES = "UPDATE_TRANSFER_USAGES"
}

export interface LoadTransferUsagePayload {
  query?: {
    show_all?: boolean;
  };
}

export interface LoadTransferUsageData {
  transfer_usages: TransferUsage[];
}

export enum LoadTransferUsagesActionTypes {
  LOAD_TRANSFER_USAGES_REQUEST = "LOAD_TRANSFER_USAGES_REQUEST",
  LOAD_TRANSFER_USAGES_SUCCESS = "LOAD_TRANSFER_USAGES_SUCCESS",
  LOAD_TRANSFER_USAGES_FAILURE = "LOAD_TRANSFER_USAGES_FAILURE"
}
