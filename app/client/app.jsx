import "babel-polyfill";
import "react-dates/initialize";

import React from "react";
import { Provider } from "react-redux";
import { createBrowserHistory } from "history";

import store from "./createStore.js";
import Nav from "./nav.jsx";

export const browserHistory = createBrowserHistory({});

export default class App extends React.Component {
  render() {
    return (
      <Provider store={store}>
        <Nav />
      </Provider>
    );
  }
}
