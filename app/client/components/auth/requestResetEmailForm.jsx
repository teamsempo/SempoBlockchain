import React from "react";
import { connect } from "react-redux";

import AsyncButton from "./../AsyncButton.jsx";

import { ResetPasswordEmailAction } from "../../reducers/auth/actions";

import { Input, ErrorMessage } from "./../styledElements";

const mapStateToProps = state => {
  return {
    email_state: state.requestResetEmailState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    requestPasswordResetEmail: payload =>
      dispatch(ResetPasswordEmailAction.passwordResetEmailRequest(payload))
  };
};

class RequestResetEmailFormContainer extends React.Component {
  constructor() {
    super();
    this.state = {
      email: "",
      email_missing: false
    };
  }

  attemptRequestPasswordResetEmail() {
    if (this.state.email === "") {
      this.setState({ email_missing: false });
      return;
    }
    this.props.requestPasswordResetEmail({ body: { email: this.state.email } });
  }

  onEmailFieldKeyPress(e) {
    let email = e.target.value;
    this.setState({ error: false, email: email });
    if (e.nativeEvent.keyCode !== 13) return;
    this.attemptRequestPasswordResetEmail(email);
  }

  onClick() {
    this.attemptRequestPasswordResetEmail(this.state.email);
  }

  render() {
    return (
      <RequestResetEmailForm
        onEmailFieldKeyPress={e => this.onEmailFieldKeyPress(e)}
        onClick={() => this.onClick()}
        email_missing={this.state.email_missing}
        requestError={this.props.email_state.error}
        requestSuccess={this.props.email_state.success}
        isLoading={this.props.email_state.isRequesting}
      />
    );
  }
}

const RequestResetEmailForm = function(props) {
  if (props.email_missing) {
    var error_message = "Email Missing";
  } else if (props.requestError) {
    error_message = props.requestError;
  } else {
    error_message = "";
  }

  if (props.requestSuccess) {
    var innercontent = (
      <div>We've sent you an email to reset your password.</div>
    );
  } else {
    innercontent = (
      <div>
        <Input
          type="email"
          id="UserField"
          onKeyUp={props.onEmailFieldKeyPress}
          placeholder="Email"
          aria-label="Email"
        />

        <AsyncButton
          onClick={props.onClick}
          isLoading={props.isLoading}
          buttonStyle={{ width: "calc(100% - 1em)", display: "flex" }}
          buttonText={<span>Reset Password</span>}
          label={"Reset Password on Sempo Dashboard"}
        />
        <ErrorMessage>{error_message}</ErrorMessage>
      </div>
    );
  }

  return (
    <div style={{ textAlign: "center" }}>
      <h3> Reset Password </h3>

      {innercontent}
    </div>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(RequestResetEmailFormContainer);
