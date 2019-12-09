import 'babel-polyfill';
import 'react-dates/initialize';

import React from 'react';
import { createStore, applyMiddleware, compose } from 'redux'
import { connect, Provider } from 'react-redux';
import createSagaMiddleware from 'redux-saga'
import { delayConfiguration } from 'pusher-redux';
import * as Sentry from '@sentry/browser';
import { createBrowserHistory } from 'history'


import appReducer from './reducers/rootReducer'
import rootsaga  from './sagas/rootSaga'

import Nav from './nav.jsx'

const sagaMiddleware = createSagaMiddleware();

// Setup redux dev tools
const composeSetup = process.env.NODE_ENV !== 'prod' && typeof window === 'object' &&
  window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ ?
  window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ : compose

export const store = createStore(
  appReducer,
  composeSetup(
    applyMiddleware(sagaMiddleware)
  )
);

// Setup sentry
Sentry.init({ dsn: window.SENTRY_REACT_DSN });

// Pusher Options
const pusherOptions = {
  cluster: 'ap1',
  authEndpoint: '/api/pusher/auth'
};

delayConfiguration(store, window.PUSHER_KEY, pusherOptions);

sagaMiddleware.run(rootsaga);

export const browserHistory = createBrowserHistory({});

export default class App extends React.Component {

  render() {
    return (
        <Provider store = {store}>
            <Nav />
        </Provider>
      )
  }
}