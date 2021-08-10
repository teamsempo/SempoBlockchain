import React from "react";
import { connect } from "react-redux";
import { Button, Input, Form } from "antd";

import { ResetPasswordEmailAction } from "../../reducers/auth/actions";

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
    this.state = {};
    this.onFinish = this.onFinish.bind(this);
  }

  onFinish(values) {
    this.props.requestPasswordResetEmail({
      body: {
        email: values.email
      }
    });
  }

  onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

  render() {
    return (
      <RequestResetEmailForm
        requestSuccess={this.props.email_state.success}
        isLoading={this.props.email_state.isRequesting}
        onFinish={this.onFinish}
        onFinishFailed={this.onFinishFailed}
      />
    );
  }
}

const RequestResetEmailForm = function(props) {
  if (props.requestSuccess) {
    var innercontent = (
      <div>We've sent you an email to reset your password.</div>
    );
  } else {
    innercontent = (
      <Form
        name="basic"
        style={{ maxWidth: "300px" }}
        onFinish={props.onFinish}
        onFinishFailed={props.onFinishFailed}
      >
        <Form.Item
          aria-label="Email"
          name="email"
          rules={[{ required: true, message: "Please enter your email!" }]}
        >
          <Input placeholder="Email" type={"email"} />
        </Form.Item>

        <Button
          htmlType="submit"
          loading={props.isLoading}
          label={"Reset Password on Sempo Dashboard"}
          type={"primary"}
          block
        >
          Reset Password
        </Button>
      </Form>
    );
  }

  return <div style={{ textAlign: "center" }}>{innercontent}</div>;
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(RequestResetEmailFormContainer);
