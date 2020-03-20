import React from 'react';

import { WrapperDiv, PageWrapper, ModuleBox } from '../styledElements';

import SideBar from '../navBar.jsx';

import CreateUserUpdated from '../user/CreateUser.tsx';

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
