import { delay } from "redux-saga";
import { call, put, select, take, takeEvery } from "redux-saga/effects";

import {
  ADD_FLASH_MESSAGE,
  SHOW_FLASH,
  CLEAR_FLASH
} from "../reducers/messageReducer";
const getMessages = state => state.message.messageList;

const FIVE_SECONDS = 5000;

export function* showFlashMessage() {
  yield put({ type: SHOW_FLASH });
  yield call(delay, FIVE_SECONDS); // wait 5 secs
  yield put({ type: CLEAR_FLASH });
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

    // wait until we get a new ADD_FLASH_MESSAGE action
    // yield put({type: ADD_FLASH_MESSAGE, message});
    // yield showFlashMessage();
  }
}

export default function* watchOnAddFlashMessage() {
  yield takeEvery(ADD_FLASH_MESSAGE, onAddFlashMessage);
}
