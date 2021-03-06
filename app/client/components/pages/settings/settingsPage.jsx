import React from "react";
import styled from "styled-components";
import { Link } from "react-router-dom";

import AuthModule from "../../auth/authModule.jsx";
import UserList from "../../adminUser/adminUserList.jsx";
import ExternalAuthCredentials from "../../externalAuthCredentials";
import GetVerified from "../../GetVerified";
import DemoGenericRedux from "../../demoGenericRedux";

import {
  WrapperDiv,
  Row,
  PageWrapper,
  ModuleHeader,
  RestrictedModuleBox
} from "../../styledElements";

export default class settingsPage extends React.Component {
  render() {
    return (
      <WrapperDiv>
        <DemoGenericRedux />
        <PageWrapper style={{ display: "flex", flexDirection: "column" }}>
          <Row>
            <RestrictedModuleBox>
              <ModuleHeader>SETTINGS</ModuleHeader>
              <p style={{ margin: "1em" }}></p>
              <ExternalAuthCredentials />
              <GetVerified />
              <PageLink to="/settings/project" headerText="Project Settings">
                Update your project settings
              </PageLink>
            </RestrictedModuleBox>

            <RestrictedModuleBox>
              <ModuleHeader>Account Management</ModuleHeader>
              <PageLink
                to="/settings/change-password"
                headerText="Change Password"
              >
                Change your account password
              </PageLink>
              <PageLink
                to="/settings/tfa"
                headerText="Two-step authentication "
              >
                Secure your account with two step authentication
              </PageLink>
              <AuthModule />
            </RestrictedModuleBox>
          </Row>

          <Row>
            <RestrictedModuleBox style={{ width: "100%", overflow: "visible" }}>
              <UserList />
            </RestrictedModuleBox>
          </Row>

          <br />
          <br />

          <BuildHash>Build ID: {window.BUILD_HASH}</BuildHash>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

const PageLink = props => (
  <StyledAccountWrapper to={props.to}>
    <StyledHeader>{props.headerText}</StyledHeader>
    <StyledContent>
      <i>{props.children}</i>
    </StyledContent>
  </StyledAccountWrapper>
);

const StyledHeader = styled.div`
  font-weight: 600;
  margin: 0 0 0.6em;
`;

const StyledContent = styled.div`
  font-weight: 400;
  margin: 0;
`;

const StyledAccountWrapper = styled(Link)`
  display: flex;
  background-color: #f7fafc;
  padding: 1em;
  font-size: 14px;
  border: 1px solid #dbe4e8;
  text-decoration: none;
  flex-direction: column;
  margin: 1em;
  color: #555555;
  &:hover {
    text-decoration: underline;
  }
`;

const BuildHash = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  font-size: 0.8em;
  padding: 1.2em;
  margin-left: 234px;
  @media (max-width: 767px) {
    margin: 0;
  }
`;
