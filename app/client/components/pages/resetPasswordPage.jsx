import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import ResetPasswordForm from "../auth/resetPasswordForm.jsx";
import LoadingSpinner from "../loadingSpinner.jsx";
import SideBar from "../navBar.jsx";

import { ModuleBox, ModuleHeader } from "../styledElements";

const mapStateToProps = state => {
  return {};
};

const mapDispatchToProps = dispatch => {
  return {};
};

class resetPasswordPage extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    return (
      <WrapperDiv>
        <ModuleBox style={{ width: "50%", maxWidth: "350px", padding: "40px" }}>
          <ModuleHeader>Reset Password</ModuleHeader>
          <ResetPasswordForm requireOldPassword={false} />
        </ModuleBox>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(resetPasswordPage);

const WrapperDiv = styled.div`
  width: 100vw;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;
