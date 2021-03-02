import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { NavLink } from "react-router-dom";
import ReactPasswordStrength from "react-password-strength";

import { ResetPasswordAction } from "../../reducers/auth/actions";

import AsyncButton from "./../AsyncButton.jsx";

import { Input, ErrorMessage } from "./../styledElements";

import { parseQuery } from "../../utils";

const mapStateToProps = state => {
  return {
    resetPasswordState: state.resetPasswordState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    resetPassword: payload =>
      dispatch(ResetPasswordAction.resetPasswordRequest(payload))
  };
};

class ResetPasswordFormContainer extends React.Component {
  constructor() {
    super();
    this.state = {
      new_password: "",
      reenter_password: "",
      old_password: null,
      passwordIsValid: false,
      password_missing: false,
      password_missmatch: false,
      password_invalid: false,
      reset_password_token: null
    };
  }

  componentDidMount() {
    const parsed = parseQuery(location.search);
    if (parsed.token) {
      console.log(parsed.token);
      this.setState({ reset_password_token: parsed.token });
    }
  }

  attemptReset() {
    if (this.state.new_password == "") {
      this.setState({ password_missing: true });
      return;
    }

    if (this.state.new_password != this.state.reenter_password) {
      this.setState({ password_missmatch: true });
      return;
    }

    if (!this.state.passwordIsValid) {
      this.setState({ password_invalid: true });
      return;
    }

    this.props.resetPassword({
      body: {
        new_password: this.state.new_password,
        reset_password_token: this.state.reset_password_token,
        old_password: this.state.old_password
      }
    });
  }

  onOldPasswordFieldKeyPress(e) {
    let old_password = e.target.value;
    this.setState({ old_password: old_password });
    if (e.nativeEvent.keyCode !== 13) return;
  }

  onNewPasswordFieldKeyPress(e) {
    var password = e.password;
    var isValid = e.isValid;
    this.setState({
      new_password: password,
      password_missing: false,
      passwordIsValid: isValid
    });
  }

  onReenterPasswordFieldKeyPress(e) {
    let reenter_password = e.target.value;
    this.setState({
      reenter_password: reenter_password,
      password_missmatch: false
    });
    if (e.nativeEvent.keyCode !== 13) return;
    this.attemptReset();
  }

  onClick() {
    this.attemptReset();
  }

  render() {
    if (this.props.resetPasswordState.success) {
      return (
        <div style={{ textAlign: "center" }}>
          <h3> Password Successfuly Changed </h3>
          <Text>
            You can now{" "}
            <StyledLink to="/" exact>
              Login
            </StyledLink>
          </Text>
        </div>
      );
    }

    return (
      <ResetPasswordForm
        requireOldPassword={this.props.requireOldPassword}
        onOldPasswordFieldKeyPress={e => this.onOldPasswordFieldKeyPress(e)}
        onNewPasswordFieldKeyPress={e => this.onNewPasswordFieldKeyPress(e)}
        onReenterPasswordFieldKeyPress={e =>
          this.onReenterPasswordFieldKeyPress(e)
        }
        onClick={() => this.onClick()}
        invalid_username={this.state.invalid_username}
        password_missing={this.state.password_missing}
        password_missmatch={this.state.password_missmatch}
        password_invalid={this.state.password_invalid}
        invalid_reset={this.props.resetPasswordState.error}
      />
    );
  }
}

const ResetPasswordForm = function(props) {
  if (props.password_missing) {
    var error_message = "Password Missing";
  } else if (props.password_missmatch) {
    error_message = "Passwords do not match";
  } else if (props.password_invalid) {
    error_message = "Password too weak";
  } else if (props.invalid_reset) {
    error_message = props.invalid_reset;
  } else {
    error_message = "";
  }

  if (props.requireOldPassword) {
    var oldPasswordSection = (
      <div style={{ textAlign: "center" }}>
        Your current password:
        <Input
          type="password"
          onKeyUp={props.onOldPasswordFieldKeyPress}
          placeholder="Password"
          aria-label="Password"
        />
      </div>
    );
  } else {
    oldPasswordSection = <div></div>;
  }

  return (
    <div style={{ textAlign: "center" }}>
      {oldPasswordSection}
      Enter a new password:
      <ReactPasswordStrength
        minLength={8}
        type="password"
        changeCallback={data => props.onNewPasswordFieldKeyPress(data)}
        inputProps={{ placeholder: "Password" }}
        className={"default-input"}
      />
      <Input
        type="password"
        onKeyUp={props.onReenterPasswordFieldKeyPress}
        placeholder="Retype Password"
        aria-label="Retype Password"
      />
      <ErrorMessage>{error_message}</ErrorMessage>
      <AsyncButton
        onClick={props.onClick}
        isLoading={props.isRegistering}
        buttonStyle={{ width: "calc(100% - 1em)", display: "flex" }}
        buttonText={<span>Change Password</span>}
        label={"Change Password"}
      />
    </div>
  );
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(ResetPasswordFormContainer);

const Text = styled.p`
  margin: 0.5em;
  text-align: center;
`;

const StyledLink = styled(NavLink)`
  color: #30a4a6;
  font-weight: bolder;
  &:hover {
    text-decoration: underline;
  }
`;
