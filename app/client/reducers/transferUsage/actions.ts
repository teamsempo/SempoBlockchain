import {
  LOAD_TRANSFER_USAGES_REQUEST,
  LoadTransferUsagePayload,
  LoadTransferUsagesAction
} from "./types";

export const loadTransferUsages = (
  payload: LoadTransferUsagePayload
): LoadTransferUsagesAction => ({
  type: LOAD_TRANSFER_USAGES_REQUEST,
  payload
});
