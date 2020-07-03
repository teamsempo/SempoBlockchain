import { MessageAction } from "../../../reducers/message/actions";
import { onAddFlashMessage } from "../../../sagas/messageSaga";
import { recordSaga } from "../../setup/testUtils";
import { AddMessageData } from "../../../__fixtures__/message/messageData";
import {
  initialMessageState,
  message
} from "../../../reducers/message/reducers";

describe("messageSaga", () => {
  it("onAddFlashMessage - no messages", async () => {
    const dispatched = await recordSaga(onAddFlashMessage, null, {
      message: initialMessageState
    });

    expect(dispatched).toEqual([]);
  });

  it("onAddFlashMessage - one message", async () => {
    const updatedState = message(
      initialMessageState,
      MessageAction.addMessage(AddMessageData)
    );

    const dispatched = await recordSaga(onAddFlashMessage, null, {
      message: updatedState
    });

    expect(dispatched).toEqual([MessageAction.showFlash()]);
  });
});
