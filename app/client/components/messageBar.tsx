import React, {useState} from "react";
import { useSelector } from "react-redux";
import styled from "styled-components";
import { PageWrapper } from "./styledElements.js";
import { ReduxState } from "../reducers/rootReducer";

export default function MessageBar() {
  const loggedIn = useSelector((state: ReduxState) => state.login.token != null);
  const message = useSelector((state: ReduxState) => state.message);

  return (
    <PageWrapper
      style={{
        marginLeft: loggedIn ? undefined : "auto",
        width: loggedIn ? undefined : "100vw",
        transitionProperty: "all",
        transitionDuration: "1.5s",
        transitionTimingFunction: "cubic-bezier(0, 1, 0.5, 1)",
        top: message.showMessage ? 0 : -35,
        position: "fixed",
        zIndex: 99,
        textAlign: "center"
      }}
    >
      <Message
        style={{
          backgroundColor: message.error ? "#F44336" : "#2D9EA0",
          opacity: message.showMessage ? 1 : 0
        }}
      >
        {message.messageList[0]}
      </Message>
    </PageWrapper>
  );
}

const Message = styled.p`
  width: calc(100% - 3em);
  margin: 1em auto;
  padding: 0.5em;
  font-weight: 500;
  color: white;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  max-width: 300px;
  transition-property: all;
  transition-duration: 0.25s;
  transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
`;
