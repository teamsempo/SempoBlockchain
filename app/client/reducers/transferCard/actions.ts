import { EditTransferCardActionTypes, EditTransferCardPayload } from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const EditTransferCardAction = {
  editTransferCardRequest: (payload: EditTransferCardPayload) =>
    createAction(
      EditTransferCardActionTypes.EDIT_TRANSFER_CARD_REQUEST,
      payload
    ),
  editTransferCardSuccess: () =>
    createAction(EditTransferCardActionTypes.EDIT_TRANSFER_CARD_SUCCESS),
  editTransferCardFailure: (error: string) =>
    createAction(EditTransferCardActionTypes.EDIT_TRANSFER_CARD_FAILURE, error)
};
export type EditTransferCardAction = ActionsUnion<
  typeof EditTransferCardAction
>;
