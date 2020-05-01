import { MessageActionTypes } from "./types";
import { MessageAction } from "./actions";

interface MessageState {
  showMessage: boolean;
  messageList: string[];
  error: boolean;
}

const initialMessageState: MessageState = {
  showMessage: false,
  messageList: [],
  error: false
};

export const message = (state = initialMessageState, action: MessageAction) => {
  switch (action.type) {
    case MessageActionTypes.ADD_FLASH_MESSAGE:
      return {
        ...state,
        error: action.payload.error,
        messageList: [...state.messageList, action.payload.message]
      };
    case MessageActionTypes.SHOW_FLASH:
      return { ...state, showMessage: true };
    case MessageActionTypes.CLEAR_FLASH:
      return {
        ...state,
        showMessage: false,
        messageList: state.messageList.slice(1),
        error: false
      };
    default:
      return state;
  }
};
