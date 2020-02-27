import {
  LOAD_TRANSFER_USAGES_REQUEST,
  LoadTransferUsagesAction
} from "./types";

export const loadTransferUsages = (): LoadTransferUsagesAction => ({
  type: LOAD_TRANSFER_USAGES_REQUEST
});
