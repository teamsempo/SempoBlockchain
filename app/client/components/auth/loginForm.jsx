import React from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Button, Input, Form, Typography } from "antd";

import { LoginAction } from "../../reducers/auth/actions";

import TFAForm from "./TFAForm.jsx";

const { Text } = Typography;

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
    this.state = {};
    this.onFinish = this.onFinish.bind(this);
  }

  onFinish(values) {
    this.props.loginRequest({
      body: {
        username: values.email,
        password: values.password
      }
    });
  }

  onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

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
        isLoading={this.props.login_status.isLoggingIn}
        onFinish={this.onFinish}
        onFinishFailed={this.onFinishFailed}
      />
    );
  }
}

const LoginForm = function(props) {
  return (
    <div>
      <Form
        name="basic"
        style={{ maxWidth: "300px" }}
        initialValues={{ remember: false }}
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
        <Form.Item
          aria-label="Password"
          name="password"
          rules={[{ required: true, message: "Please enter your password!" }]}
        >
          <Input
            placeholder="Password"
            type={"password"}
            suffix={<Link to={"/login/forgot"}>Forgot Password</Link>}
          />
        </Form.Item>

        <Button
          htmlType="submit"
          loading={props.isLoading}
          label={"Login"}
          type={"primary"}
          block
        >
          Login
        </Button>
      </Form>
      <div style={{ textAlign: "center", marginTop: "24px" }}>
        <Text>Don’t have a Sempo account?</Text>{" "}
        <Link to={"/login/sign-up"}>Sign Up</Link>
      </div>
    </div>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(LoginFormContainer);
