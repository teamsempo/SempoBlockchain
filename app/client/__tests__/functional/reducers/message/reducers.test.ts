import "../../../setup/setupTests.js";
import {
  message,
  initialMessageState,
  MessageState
} from "../../../../reducers/message/reducers";
import { AddMessageData } from "../../../../__fixtures__/message/messageData";
import { MessageAction } from "../../../../reducers/message/actions";

describe("message reducer", () => {
  let updatedState: MessageState;

  beforeEach(() => {
    updatedState = message(
      initialMessageState,
      MessageAction.addMessage(AddMessageData)
    );
  });

  it("add single message", () => {
    expect(updatedState.messageList).toHaveLength(1);
    expect(updatedState.messageList).toEqual([AddMessageData.message]);
  });

  it("add second message", () => {
    const secondMessageState = message(
      updatedState,
      MessageAction.addMessage(AddMessageData)
    );
    expect(secondMessageState.messageList).toHaveLength(2);
  });

  it("show flash", () => {
    const showFlashState = message(updatedState, MessageAction.showFlash());
    expect(showFlashState.showMessage).toEqual(true);
  });

  it("add second message, clear flash", () => {
    const secondMessageState = message(
      updatedState,
      MessageAction.addMessage(AddMessageData)
    );
    expect(secondMessageState.messageList).toHaveLength(2);

    const clearFlashState = message(
      secondMessageState,
      MessageAction.clearFlash()
    );
    expect(clearFlashState.messageList).toHaveLength(1);
    expect(clearFlashState.showMessage).toEqual(false);
  });
});
