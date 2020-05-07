import { AddMessagePayload, MessageActionTypes } from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const MessageAction = {
  addMessage: (payload: AddMessagePayload) =>
    createAction(MessageActionTypes.ADD_FLASH_MESSAGE, payload),
  showFlash: () => createAction(MessageActionTypes.SHOW_FLASH),
  clearFlash: () => createAction(MessageActionTypes.CLEAR_FLASH)
};
export type MessageAction = ActionsUnion<typeof MessageAction>;
