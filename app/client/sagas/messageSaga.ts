import { put, select, takeEvery, delay, all } from "redux-saga/effects";

import { ReduxState } from "../reducers/rootReducer";
import { MessageAction } from "../reducers/message/actions";
import { MessageActionTypes } from "../reducers/message/types";

const getMessages = (state: ReduxState) => state.message.messageList;

const FIVE_SECONDS = 5000;

export function* showFlashMessage() {
  yield put(MessageAction.showFlash());
  yield delay(FIVE_SECONDS); // wait 5 secs
  yield put(MessageAction.clearFlash());
}

export function* onAddFlashMessage() {
  while (true) {
    const flashQueue = yield select(getMessages);

    // empty whats in the queue first
    if (flashQueue.length > 0) {
      while (true) {
        const queue = yield select(getMessages);
        if (queue.length === 0) {
          break;
        }

        yield showFlashMessage();
      }
    }
  }
}

function* watchOnAddFlashMessage() {
  yield takeEvery([MessageActionTypes.ADD_FLASH_MESSAGE], onAddFlashMessage);
}

export default function* messageSagas() {
  yield all([watchOnAddFlashMessage()]);
}
