import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import { LoginAction } from "../../reducers/auth/actions";

import { StyledButton, PlainTextButton } from "./../styledElements";

import LoginForm from "./loginForm.jsx";
import RegisterForm from "./registerForm.jsx";
import RequestResetEmailForm from "./requestResetEmailForm.jsx";

const mapStateToProps = state => {
  return {
    loggedIn: state.login.token != null,
    loginData: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    logout: () => dispatch(LoginAction.apiLogout())
  };
};

class authModuleContainer extends React.Component {
  constructor() {
    super();
    this.state = {
      moduleActive: false,
      activeForm: "LOGIN"
    };
  }

  setActiveForm(form) {
    this.setState({ moduleActive: true, activeForm: form });
  }

  deactivateAuthModule() {
    this.setState({ moduleActive: false });
  }

  render() {
    if (this.props.loggedIn) {
      var button = (
        <div style={{ margin: "auto 1em" }}>
          <StyledButton onClick={this.props.logout} label={"Logout Admin"}>
            Logout Admin
          </StyledButton>
        </div>
      );
    } else {
      var button = (
        <div style={{ margin: "auto 1em" }}>
          <StyledButton
            onClick={() => this.setActiveForm("LOGIN")}
            label={"Go to Login Page"}
          >
            Login
          </StyledButton>
          <StyledButton
            onClick={() => this.setActiveForm("REGISTER")}
            label={"Go to Register Page"}
          >
            Register
          </StyledButton>
        </div>
      );
    }

    return (
      <div>
        {button}
        <AuthModule
          props={{
            moduleActive: this.state.moduleActive,
            activeForm: this.state.activeForm,
            setActiveForm: form => this.setActiveForm(form),
            deactivateAuthModule: () => this.deactivateAuthModule(),
            loggedIn: this.props.loggedIn
          }}
        />
      </div>
    );
  }
}

const AuthModule = function({ props }) {
  if (props.loggedIn) {
    var formcontents = (
      <ModalContent>
        Success!
        <BottomRow>
          <PlainTextButton onClick={props.deactivateAuthModule}>
            Close
          </PlainTextButton>
        </BottomRow>
      </ModalContent>
    );
  } else if (props.activeForm === "REGISTER") {
    var formcontents = (
      <ModalContent>
        <RegisterForm />
        <BottomRow>
          <PlainTextButton onClick={() => props.setActiveForm("LOGIN")}>
            Already Registered? Login
          </PlainTextButton>
          <PlainTextButton onClick={props.deactivateAuthModule}>
            Close
          </PlainTextButton>
        </BottomRow>
      </ModalContent>
    );
  } else if (props.activeForm === "LOGIN") {
    formcontents = (
      <ModalContent>
        <LoginForm />
        <BottomRow>
          <PlainTextButton onClick={() => props.setActiveForm("REGISTER")}>
            No account? Register
          </PlainTextButton>
          <PlainTextButton onClick={() => props.setActiveForm("RESET")}>
            Forgotten Password?
          </PlainTextButton>
          <PlainTextButton onClick={props.deactivateAuthModule}>
            Close
          </PlainTextButton>
        </BottomRow>
      </ModalContent>
    );
  } else if (props.activeForm === "RESET") {
    formcontents = (
      <ModalContent>
        <RequestResetEmailForm />
        <BottomRow>
          <PlainTextButton onClick={() => props.setActiveForm("LOGIN")}>
            Login
          </PlainTextButton>
          <PlainTextButton onClick={props.deactivateAuthModule}>
            Close
          </PlainTextButton>
        </BottomRow>
      </ModalContent>
    );
  }

  if (props.moduleActive && !props.loggedIn) {
    return (
      <Modal>
        {formcontents}
        <div
          style={{ width: "100%", height: "100%" }}
          onClick={props.deactivateAuthModule}
        ></div>
      </Modal>
    );
  } else {
    return <div></div>;
  }
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(authModuleContainer);

const Modal = styled.div`
  position: fixed; /* Stay in place */
  z-index: 1; /* Sit on top */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgb(0, 0, 0); /* Fallback color */
  background-color: rgba(0, 0, 0, 0.4); /* Black w/ opacity */
`;

const ModalContent = styled.div`
  background-color: #fefefe;
  margin: 15% auto; /* 15% from the top and centered */
  padding: 20px;
  border: 1px solid #888;
  width: 80%; /* Could be more or less, depending on screen size */
`;

const BottomRow = styled.div`
  display: flex;
  justify-content: space-between;
`;
