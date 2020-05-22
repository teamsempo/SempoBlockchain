import { createStore, applyMiddleware, compose } from "redux";
import createSagaMiddleware from "redux-saga";
import { delayConfiguration } from "pusher-redux";
import { createBrowserHistory } from "history";
import * as Sentry from "@sentry/browser";
import { version } from "../package.json";

import appReducer from "./reducers/rootReducer";
import rootSaga from "./sagas/rootSaga";

const sagaMiddleware = createSagaMiddleware();
export const browserHistory = createBrowserHistory({});

// Setup redux dev toolio
const composeSetup =
  process.env.NODE_ENV !== "prod" &&
  typeof window === "object" &&
  window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__
    ? window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__
    : compose;

const store = createStore(
  appReducer,
  composeSetup(applyMiddleware(sagaMiddleware))
);
export default store;

// Setup sentry
Sentry.init({
  dsn: window.SENTRY_REACT_DSN,
  release: "sempo-blockchain-react@" + version
});

// Pusher Options
const pusherOptions = {
  cluster: "ap1"
};

delayConfiguration(store, window.PUSHER_KEY, pusherOptions);

sagaMiddleware.run(rootSaga);
