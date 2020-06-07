import React from "react";
import styled from "styled-components";
import { useSelector } from "react-redux";
import Intercom, { IntercomAPI } from "react-intercom";
import { ReduxState } from "../reducers/rootReducer";

export function CustomerSupport() {
  const login = useSelector((state: ReduxState) => state.login);
  const activeOrganisation = useSelector((state: ReduxState) => state.login.organisationId ? state.organisations.byId[state.login.organisationId] : null);
  function openChat() {
    IntercomAPI("show");
  }

  const user = {
    user_id: login.userId,
    user_hash: login.intercomHash,
    name: login.email,
    company: {
      id: login.organisationId,
      name: activeOrganisation?.name
    }
  };

  return (
    <div style={{ margin: "1em" }}>
      <StyledAccountWrapper>
        <StyledHeader>Support:</StyledHeader>
        <StyledContent onClick={openChat}>
          <IconSVG src="/static/media/question-speech-bubble.svg" />
          Chat
        </StyledContent>
        <StyledContent href="http://help.withsempo.com/en/" target="_blank">
          <IconSVG src="/static/media/open-book.svg" />
          Help Center
        </StyledContent>
      </StyledAccountWrapper>
      <Intercom appID="kowgw7cm" {...user} />
    </div>
  );

}

const IconSVG = styled.img`
  width: 21px;
  padding: 0 0.5em 0 0;
  display: flex;
`;

const StyledHeader = styled.p`
  font-weight: 600;
  margin: 0 0 0.6em;
`;

const StyledContent = styled.a`
  color: #555;
  text-decoration: none;
  font-weight: 400;
  display: flex;
  align-items: center;
  margin: 0.5em 0;
  &:hover {
    text-decoration: underline;
  }
`;

const StyledAccountWrapper = styled.div`
  background-color: #f7fafc;
  padding: 1em;
  font-size: 14px;
  border: 1px solid #dbe4e8;
`;
