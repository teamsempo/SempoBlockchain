import React, { useEffect } from "react";
import { connect } from "react-redux";
import { PasswordInput } from "antd-password-input-strength";
import { Button, Input, Form } from "antd";

import { RegisterAction } from "../../reducers/auth/actions";

import TFAForm from "./TFAForm.jsx";

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

const RegisterFormContainer = props => {
  const [form] = Form.useForm();
  useEffect(() => {
    form.setFieldsValue({
      email: props.email
    });
  }, [props.email]);

  const onFinish = values => {
    props.registerRequest({
      body: {
        username: values.email,
        password: values.password,
        referral_code: props.referralCode
      }
    });
  };

  const onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

  if (props.login_status.tfaURL || props.login_status.tfaFailure) {
    return (
      <div style={{ margin: "1em" }}>
        <div style={{ textAlign: "center" }}>
          Two-Step Authentication Required
        </div>
        <TFAForm tfaURL={props.login_status.tfaURL} />
      </div>
    );
  }

  if (props.register_status.success) {
    return (
      <div>
        <h3> Register Success </h3>
        <div> We've sent you an activation email</div>
      </div>
    );
  }

  return (
    <Form
      form={form}
      name="basic"
      style={{ maxWidth: "300px" }}
      onFinish={onFinish}
      onFinishFailed={onFinishFailed}
    >
      <p
        style={
          props.email
            ? { margin: "1em 0.5em", textAlign: "center", fontWeight: 600 }
            : { display: "none" }
        }
      >
        Please choose a password
      </p>
      <Form.Item
        aria-label="Email"
        name="email"
        rules={[{ required: true, message: "Please enter your email!" }]}
      >
        <Input
          placeholder="Email"
          type={"email"}
          disabled={props.email ? "disabled" : ""}
        />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value) {
                return Promise.reject("Please enter your password!");
              }
              if (value && value.length < 8) {
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
          loading={props.register_status.isRequesting}
          label={"Register for Sempo Dashboard"}
          type={"primary"}
          block
        >
          Register
        </Button>
      </Form.Item>
    </Form>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(RegisterFormContainer);
