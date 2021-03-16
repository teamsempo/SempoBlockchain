import React from "react";
import { connect } from "react-redux";
import ReactPasswordStrength from "react-password-strength";

import { RegisterAction } from "../../reducers/auth/actions";

import AsyncButton from "./../AsyncButton.jsx";
import TFAForm from "./TFAForm.jsx";

import { Input, ErrorMessage } from "./../styledElements";

const mapStateToProps = state => {
  return {
    register_status: state.register,
    login_status: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    registerRequest: payload =>
      dispatch(RegisterAction.registerRequest(payload))
  };
};

class RegisterFormContainer extends React.Component {
  constructor() {
    super();
    this.state = {
      username: "",
      password: "",
      reenter_password: "",
      passwordIsValid: false,
      user_missing: false,
      invalid_username: false,
      password_missing: false,
      password_missmatch: false,
      invalid_register: false,
      password_invalid: false,
      invite: false
    };
  }

  componentWillMount() {
    if (this.props.email != null) {
      this.setState({ username: this.props.email, invite: true });
    }
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.email != null) {
      this.setState({ username: nextProps.email, invite: true });
    }
    this.setState({ invalid_register: nextProps.register_status.error });
  }

  attemptregister() {
    var invalid_email =
      this.state.username.match(
        /^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/
      ) == null;

    if (this.state.username === "") {
      this.setState({ user_missing: true });
      return;
    }
    if (invalid_email) {
      this.setState({ invalid_username: true });
      return;
    }

    if (this.state.password === "") {
      this.setState({ password_missing: true });
      return;
    }

    if (!this.state.passwordIsValid) {
      this.setState({ password_invalid: true });
      return;
    }

    if (this.state.password !== this.state.reenter_password) {
      this.setState({ password_missmatch: true });
      return;
    }

    this.props.registerRequest({
      body: {
        username: this.state.username,
        password: this.state.password,
        referral_code: this.props.referralCode
      }
    });
  }

  onUserFieldKeyPress(e) {
    var username = e.target.value;
    this.setState({ username: username, user_missing: false });
    if (e.nativeEvent.keyCode != 13) return;
    this.attemptregister();
  }

  onPasswordFieldKeyPress(e) {
    var password = e.password;
    var isValid = e.isValid;
    this.setState({
      password: password,
      password_missing: false,
      passwordIsValid: isValid
    });
  }

  onReenterPasswordFieldKeyPress(e) {
    var reenter_password = e.target.value;
    this.setState({
      reenter_password: reenter_password,
      password_missmatch: false
    });
    if (e.nativeEvent.keyCode != 13) return;
    this.attemptregister();
  }

  onClick() {
    this.attemptregister();
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

    if (this.props.register_status.success) {
      return (
        <div>
          <h3> Register Success </h3>
          <div> We've sent you an activation email</div>
        </div>
      );
    }

    return (
      <RegisterForm
        onUserFieldKeyPress={e => this.onUserFieldKeyPress(e)}
        onPasswordFieldKeyPress={e => this.onPasswordFieldKeyPress(e)}
        onReenterPasswordFieldKeyPress={e =>
          this.onReenterPasswordFieldKeyPress(e)
        }
        onClick={() => this.onClick()}
        user_missing={this.state.user_missing}
        invalid_username={this.state.invalid_username}
        password_missing={this.state.password_missing}
        password_missmatch={this.state.password_missmatch}
        password_invalid={this.state.password_invalid}
        invalid_register={this.state.invalid_register}
        isRegistering={this.props.register_status.isRequesting}
        state={this.state}
      />
    );
  }
}

const RegisterForm = function(props) {
  if (props.user_missing) {
    var error_message = "Email Missing";
  } else if (props.invalid_username) {
    error_message = "Invalid Email";
  } else if (props.password_missing) {
    error_message = "Password Missing";
  } else if (props.password_missmatch) {
    error_message = "Passwords do not match";
  } else if (props.invalid_register) {
    error_message = props.invalid_register;
  } else if (props.password_invalid) {
    error_message = "Password too weak";
  } else {
    error_message = "";
  }

  return (
    <div>
      <div style={{ display: "block" }}>
        <p
          style={
            props.state.invite
              ? { margin: "1em 0.5em", textAlign: "center" }
              : { display: "none" }
          }
        >
          {props.state.username}
        </p>

        <p
          style={
            props.state.invite
              ? { margin: "1em 0.5em", textAlign: "center", fontWeight: 600 }
              : { display: "none" }
          }
        >
          Please choose a password
        </p>

        <Input
          type="email"
          onKeyUp={props.onUserFieldKeyPress}
          placeholder="Email"
          disabled={props.state.invite ? "disabled" : ""}
          style={props.state.invite ? { display: "none" } : null}
          aria-label="Email"
        />

        <ReactPasswordStrength
          minLength={8}
          type="password"
          changeCallback={data => props.onPasswordFieldKeyPress(data)}
          inputProps={{ placeholder: "Password" }}
          className={"default-input"}
        />

        <Input
          type="password"
          onKeyUp={props.onReenterPasswordFieldKeyPress}
          placeholder="Retype Password"
          aria-label="Password"
        />

        <ErrorMessage>{error_message}</ErrorMessage>
      </div>

      <AsyncButton
        onClick={props.onClick}
        isLoading={props.isRegistering}
        buttonStyle={{ width: "calc(100% - 1em)", display: "flex" }}
        buttonText={<span>REGISTER</span>}
        label={"Register for Sempo Dashboard"}
      />
    </div>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(RegisterFormContainer);
