import "../../../setup/setupTests.js";
import store from "../../../../createStore.js";
import { MessageActionTypes } from "../../../../reducers/message/types";
import { MessageAction } from "../../../../reducers/message/actions";
import { AddMessageData } from "../../../../__fixtures__/message/messageData";

describe("add message redux", () => {
  beforeEach(() => {
    store.clearActions();
  });

  it("should dispatch the addMessage action", () => {
    const expectedActions = [
      {
        payload: AddMessageData,
        type: MessageActionTypes.ADD_FLASH_MESSAGE
      }
    ];
    store.dispatch(MessageAction.addMessage(AddMessageData));

    expect(store.getActions()).toEqual(expectedActions);
  });

  it("should dispatch the showFlash action", () => {
    const expectedActions = [
      {
        type: MessageActionTypes.SHOW_FLASH
      }
    ];
    store.dispatch(MessageAction.showFlash());

    expect(store.getActions()).toEqual(expectedActions);
  });

  it("should dispatch the clearFlash action", () => {
    const expectedActions = [
      {
        type: MessageActionTypes.CLEAR_FLASH
      }
    ];
    store.dispatch(MessageAction.clearFlash());

    expect(store.getActions()).toEqual(expectedActions);
  });
});
