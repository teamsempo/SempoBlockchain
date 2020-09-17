import React from "react";
import styled from "styled-components";

import { PageWrapper, ModuleHeader } from "../styledElements";
import InviteForm from "../adminUser/InviteForm.jsx";

export default class InvitePage extends React.Component {
  render() {
    return (
      <WrapperDiv>
        <PageWrapper style={{ display: "flex", flexDirection: "column" }}>
          <Row>
            <ModuleBox>
              <ModuleHeader>INVITE NEW ADMINS</ModuleHeader>
              <p style={{ margin: "1em" }}>
                Enter the email addresses of the administrators you'd like to
                invite, and choose the role they should have.
              </p>
              <InviteForm />
            </ModuleBox>
          </Row>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const Row = styled.div`
  display: flex;
  flex-direction: row;
  width: 100%;
  @media (max-width: 767px) {
    flex-direction: column;
    width: calc(100% - 2em);
  }
`;

const ModuleBox = styled.div`
  margin: 1em;
  background-color: #fff;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  overflow: hidden;
  position: relative;
  width: 50%;
  @media (max-width: 767px) {
    width: 100%;
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
