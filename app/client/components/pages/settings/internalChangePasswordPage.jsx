import React from 'react';
import styled from 'styled-components';

import ResetPasswordForm from '../../auth/resetPasswordForm.jsx';

import {
  PageWrapper,
  ModuleHeader,
  WrapperDiv,
  RestrictedModuleBox,
} from '../../styledElements';

export default class internalChangePasswordPage extends React.Component {
  render() {
    return (
      <WrapperDiv>
        <PageWrapper style={{ display: 'flex', flexDirection: 'column' }}>
          <RestrictedModuleBox>
            <ModuleHeader>Change password</ModuleHeader>
            <ResetPasswordForm requireOldPassword />
          </RestrictedModuleBox>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}
