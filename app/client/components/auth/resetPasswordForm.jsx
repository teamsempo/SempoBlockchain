import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { NavLink } from "react-router-dom";
import { PasswordInput } from "antd-password-input-strength";
import { Button, Input, Form } from "antd";

import { ResetPasswordAction } from "../../reducers/auth/actions";

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
      reset_password_token: null
    };
    this.onFinish = this.onFinish.bind(this);
  }

  componentDidMount() {
    const parsed = parseQuery(location.search);
    if (parsed.token) {
      console.log(parsed.token);
      this.setState({ reset_password_token: parsed.token });
    }
  }

  onFinish = values => {
    this.props.resetPassword({
      body: {
        new_password: values.password,
        reset_password_token: this.state.reset_password_token,
        old_password: values.old_password
      }
    });
  };

  onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

  render() {
    if (this.props.resetPasswordState.success) {
      return (
        <div style={{ textAlign: "center" }}>
          <h3> Password Successfully Changed </h3>
          {this.props.requireOldPassword ? null : (
            <Text>
              You can now{" "}
              <StyledLink to="/" exact>
                Login
              </StyledLink>
            </Text>
          )}
        </div>
      );
    }

    return (
      <ResetPasswordForm
        requireOldPassword={this.props.requireOldPassword}
        isLoading={this.props.resetPasswordState.isRequesting}
        onFinish={this.onFinish}
        onFinishFailed={this.onFinishFailed}
      />
    );
  }
}

const ResetPasswordForm = function(props) {
  if (props.requireOldPassword) {
    var oldPasswordSection = (
      <div style={{ textAlign: "center" }}>
        Your current password:
        <Form.Item
          name="old_password"
          rules={[{ required: true, message: "Please enter your password!" }]}
        >
          <Input.Password placeholder={"Current Password"} type={"password"} />
        </Form.Item>
      </div>
    );
  } else {
    oldPasswordSection = <div></div>;
  }

  return (
    <div>
      <Form
        name="basic"
        style={{ maxWidth: "300px" }}
        onFinish={props.onFinish}
        onFinishFailed={props.onFinishFailed}
      >
        {oldPasswordSection}
        <p style={{ textAlign: "center" }}>Enter a new password:</p>
        <Form.Item
          name="password"
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value) {
                  return Promise.reject("Please enter your password!");
                }
                if (value && value.length <= 8) {
                  return Promise.reject(
                    "Password must be at least 8 characters long"
                  );
                }
                if (value !== getFieldValue("retypePassword")) {
                  return Promise.reject("Passwords do not match");
                }
                return Promise.resolve();
              }
            })
          ]}
          aria-label="password"
          dependencies={["retypePassword"]}
        >
          <PasswordInput
            inputProps={{
              placeholder: "Password",
              minLength: "8",
              type: "password"
            }}
          />
        </Form.Item>
        <Form.Item
          name="retypePassword"
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value) {
                  return Promise.reject("Please reenter your password!");
                }
                if (value !== getFieldValue("password")) {
                  return Promise.reject("Passwords do not match");
                }
                return Promise.resolve();
              }
            })
          ]}
          dependencies={["password"]}
        >
          <Input.Password placeholder={"Retype Password"} type={"password"} />
        </Form.Item>

        <Form.Item>
          <Button
            htmlType="submit"
            loading={props.isLoading}
            label={"Change Password"}
            type={"primary"}
            block
          >
            Change Password
          </Button>
        </Form.Item>
      </Form>
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
