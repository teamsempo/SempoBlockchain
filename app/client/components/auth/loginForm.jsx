import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { Link } from "react-router-dom";

import AsyncButton from "./../AsyncButton.jsx";
import { LoginAction } from "../../reducers/auth/actions";

import { Input, ErrorMessage } from "./../styledElements";
import { Footer, FooterLink, FooterText } from "../pages/authPage.jsx";
import TFAForm from "./TFAForm.jsx";

const mapStateToProps = state => {
  return {
    login_status: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loginRequest: payload => dispatch(LoginAction.loginRequest(payload))
  };
};

export class LoginFormContainer extends React.Component {
  constructor() {
    super();
    this.state = {
      username: "",
      password: "",
      user_missing: false,
      password_missing: false,
      invalid_login: false
    };
  }

  componentWillReceiveProps(nextProps) {
    this.setState({ invalid_login: nextProps.login_status.error });
  }

  attemptlogin() {
    if (this.state.username == "") {
      this.setState({ user_missing: true });
      return;
    }
    if (this.state.password == "") {
      this.setState({ password_missing: true });
      return;
    }
    this.props.loginRequest({
      body: { username: this.state.username, password: this.state.password }
    });
  }

  onUserFieldKeyPress(e) {
    var username = e.target.value;
    this.setState({
      username: username,
      user_missing: false,
      invalid_login: false
    });
    if (e.nativeEvent.keyCode != 13) return;
    this.attemptlogin();
  }

  onPasswordFieldKeyPress(e) {
    var password = e.target.value;
    this.setState({
      password: password,
      password_missing: false,
      invalid_login: false
    });
    if (e.nativeEvent.keyCode != 13) return;
    this.attemptlogin();
  }

  onClick() {
    this.attemptlogin();
  }

  render() {
    if (this.props.login_status.tfaURL || this.props.login_status.tfaFailure) {
      return (
        <div style={{ margin: "1em" }}>
          <div style={{ textAlign: "center" }}>
            Two-Step Authentication Required
          </div>
          <TFAForm tfaURL={this.props.login_status.tfaURL} />
        </div>
      );
    }
    return (
      <LoginForm
        onUserFieldKeyPress={e => this.onUserFieldKeyPress(e)}
        onPasswordFieldKeyPress={e => this.onPasswordFieldKeyPress(e)}
        onClick={() => this.onClick()}
        user_missing={this.state.user_missing}
        password_missing={this.state.password_missing}
        invalid_login={this.state.invalid_login}
        isLoggingIn={this.props.login_status.isLoggingIn}
      />
    );
  }
}

const LoginForm = function(props) {
  if (props.user_missing) {
    var error_message = "Email Missing";
  } else if (props.password_missing) {
    error_message = "Password Missing";
  } else if (props.invalid_login) {
    error_message = props.invalid_login;
  } else {
    error_message = "";
  }

  return (
    <div>
      <div style={{ display: "block", position: "relative" }}>
        <ErrorMessage>{error_message}</ErrorMessage>

        <Input
          type="email"
          id="UserField"
          onKeyUp={props.onUserFieldKeyPress}
          placeholder="Email"
          aria-label="Email"
        />

        <Input
          type="password"
          id="PasswordField"
          onKeyUp={props.onPasswordFieldKeyPress}
          placeholder="Password"
          aria-label="Password"
        />

        <ResetPasswordLink to="/login/forgot">
          Forgot Password
        </ResetPasswordLink>
      </div>

      <AsyncButton
        onClick={props.onClick}
        isLoading={props.isLoggingIn}
        buttonStyle={{ width: "calc(100% - 1em)", display: "flex" }}
        buttonText={<span>LOGIN</span>}
        label={"Login"}
      />

      <Footer>
        <FooterText>
          Don’t have a Sempo account?
          <FooterLink to="/login/sign-up">Sign Up</FooterLink>
        </FooterText>
      </Footer>
    </div>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(LoginFormContainer);

const ResetPasswordLink = styled(Link)`
  cursor: pointer;
  font-size: 14px;
  color: #30a4a6;
  font-weight: bolder;
  text-decoration: none;
  position: absolute;
  top: 5.7em;
  right: 1em;
  &:hover {
    text-decoration: underline;
  }
`;
