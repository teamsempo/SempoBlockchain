import "babel-polyfill";

import React from "react";
import { Provider } from "react-redux";
import { IntercomProvider } from "react-use-intercom";

import store from "./createStore.js";
import Nav from "./nav.jsx";

export default class App extends React.Component {
  render() {
    return (
      <Provider store={store}>
        <IntercomProvider appId={window.INTERCOM_APP_ID}>
          <Nav />
        </IntercomProvider>
      </Provider>
    );
  }
}
