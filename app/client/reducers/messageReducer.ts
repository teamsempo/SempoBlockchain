export const ADD_FLASH_MESSAGE = "ADD_FLASH_MESSAGE";
interface AddFlashMessage {
  type: typeof ADD_FLASH_MESSAGE;
  error: boolean;
  message: string;
}
export const SHOW_FLASH = "SHOW_FLASH";
interface ShowFlash {
  type: typeof SHOW_FLASH;
}
export const CLEAR_FLASH = "CLEAR_FLASH";
interface ClearFlash {
  type: typeof CLEAR_FLASH;
}
type MessageAction = AddFlashMessage | ShowFlash | ClearFlash;

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
    case ADD_FLASH_MESSAGE:
      return {
        ...state,
        error: action.error,
        messageList: [...state.messageList, action.message]
      };
    case SHOW_FLASH:
      return { ...state, showMessage: true };
    case CLEAR_FLASH:
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
