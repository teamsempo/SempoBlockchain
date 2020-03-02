import React from "react";

import { WrapperDiv } from "../styledElements";

import SideBar from "../navBar.jsx";
import { PageWrapper, ModuleBox } from "../styledElements.js";
import CreateUserUpdated from "../user/CreateUser.tsx";

export default class createUserPage extends React.Component {
  render() {
    return (
      <WrapperDiv>
        <SideBar />
        <PageWrapper>
          <ModuleBox>
            <CreateUserUpdated />
          </ModuleBox>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}
