import React, { useState } from "react";
import { InputNumber, Modal, Form, Input, Radio } from "antd";

declare global {
  interface Window {
    CHAIN_NAMES: string;
  }
}

interface Values {
  title: string;
  description: string;
  modifier: string;
}

interface TokenModalFormProps {
  visible: boolean;
  onCreate: (values: Values) => void;
  onCancel: () => void;
}

const TokenModalForm: React.FC<TokenModalFormProps> = ({
  visible,
  onCreate,
  onCancel
}) => {
  const [form] = Form.useForm();
  const chains = window.CHAIN_NAMES && window.CHAIN_NAMES.split(",");
  return (
    <Modal
      visible={visible}
      title="Create a new token"
      okText="Create"
      cancelText="Cancel"
      onCancel={onCancel}
      onOk={() => {
        form
          .validateFields()
          .then((values: any) => {
            form.resetFields();
            onCreate(values);
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
        {/*
         // @ts-ignore */}
        <Form.Item
          tooltip="This refers to the address location of the actual token contract that manages the logic for the tokens. This does not refer to the address that holds your own personal tokens!"
          name="address"
          label="Token Address"
          rules={[
            {required: true, message: "Please input the address of token!"}
          ]}
        >
          <Input min={1} max={18} type="number"/>
        </Form.Item>
        <Form.Item
          name="modifier"
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
export default TokenModalForm;
