import React, { useEffect } from "react";
import { connect } from "react-redux";

import { InputNumber, Modal, Form, Input, Radio } from "antd";
import { CreateTokenAction } from "../../reducers/token/actions";
import { CreateToken } from "../../reducers/token/types";
import { ReduxState } from "../../reducers/rootReducer";

declare global {
  interface Window {
    CHAIN_NAMES: string;
  }
}

interface DispatchProps {
  createToken: (body: CreateToken) => CreateTokenAction;
}

interface StateProps {
  tokens: ReduxState["tokens"];
}

interface TokenModalFormProps {
  visible: boolean;
  onCancel: () => void;
}

type IProps = DispatchProps & StateProps & TokenModalFormProps;

const TokenModalForm: React.FC<IProps> = props => {
  const [form] = Form.useForm();
  const chains = window.CHAIN_NAMES && window.CHAIN_NAMES.split(",");

  useEffect(() => {
    if (
      !props.tokens.createStatus.isRequesting &&
      props.tokens.createStatus.success
    ) {
      props.onCancel();
    }
  });
  return (
    <Modal
      visible={props.visible}
      title="Create a new token"
      okText="Create"
      cancelText="Cancel"
      onCancel={props.onCancel}
      confirmLoading={props.tokens.createStatus.isRequesting}
      onOk={() => {
        form
          .validateFields()
          .then((values: any) => {
            form.resetFields();
            props.createToken(values);
          })
          .catch(info => {
            console.log("Validate Failed:", info);
          });
      }}
    >
      <Form
        form={form}
        layout="vertical"
        name="form_in_modal"
        initialValues={{ modifier: "public" }}
      >
        <Form.Item
          name="name"
          label="Token Name"
          rules={[
            { required: true, message: "Please input the name of token!" }
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="symbol"
          label="Token Symbol"
          rules={[
            { required: true, message: "Please input the name of token!" }
          ]}
        >
          <Input maxLength={4} />
        </Form.Item>
        <Form.Item
          name="decimals"
          label="Token Decimals"
          rules={[
            { required: true, message: "Please input the decimals of token!" }
          ]}
        >
          <InputNumber min={1} max={18} style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item
          tooltip="This refers to the address location of the actual token contract that
        manages the logic for the tokens. This does not refer to the address that holds your own personal tokens!"
          name="address"
          label="Token Address"
          rules={[
            { required: true, message: "Please input the address of token!" }
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="chain"
          className="collection-create-form_last-form-item"
          rules={[
            { required: true, message: "Please select the chain of the token!" }
          ]}
        >
          <Radio.Group>
            {chains &&
              chains.map((item, index) => {
                return (
                  <Radio value={item} key={index}>
                    {item}
                  </Radio>
                );
              })}
          </Radio.Group>
        </Form.Item>
      </Form>
    </Modal>
  );
};

const mapStateToProps = (state: any): StateProps => {
  return {
    tokens: state.tokens
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    createToken: (body: any) =>
      dispatch(CreateTokenAction.createTokenRequest({ body }))
  };
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TokenModalForm);
