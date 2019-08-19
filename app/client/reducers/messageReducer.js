export const ADD_FLASH_MESSAGE = 'ADD_FLASH_MESSAGE';
export const SHOW_FLASH = 'SHOW_FLASH';
export const CLEAR_FLASH = 'CLEAR_FLASH';

const initialMessageState = {
  showMessage: false,
  messageList: [],
};

export const message = (state = initialMessageState, action) => {
  switch (action.type) {
    case ADD_FLASH_MESSAGE:
        return {...state, error: action.error, messageList: [...state.messageList, action.message]};
    case SHOW_FLASH:
      return {...state, showMessage: true};
    case CLEAR_FLASH:
      return {...state, showMessage: false, messageList: state.messageList.slice(1)};
    default:
      return state;
  }
};

export const addMessage = (message) => (
    {
        type: ADD_FLASH_MESSAGE,
        message,
    }
);