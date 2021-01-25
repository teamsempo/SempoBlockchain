export interface TransferCard {
  public_serial_number: string;
  is_disabled: boolean;
}

export enum EditTransferCardActionTypes {
  EDIT_TRANSFER_CARD_REQUEST = "EDIT_TRANSFER_CARD_REQUEST",
  EDIT_TRANSFER_CARD_SUCCESS = "EDIT_TRANSFER_CARD_SUCCESS",
  EDIT_TRANSFER_CARD_FAILURE = "EDIT_TRANSFER_CARD_FAILURE"
}

export interface EditTransferCardPayload {
  body: {
    disable?: boolean;
  };
  path: string;
}
