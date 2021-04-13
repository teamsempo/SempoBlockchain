import React, { Suspense, lazy } from "react";
import {
  Modal,
  Typography,
  Button,
  Tooltip,
  Descriptions,
  Steps,
  Space,
  Form,
  Input
} from "antd";
const { Paragraph } = Typography;
const { Step } = Steps;

import { DollarCircleOutlined, QrcodeOutlined } from "@ant-design/icons";
const QRCode = lazy(() => import("qrcode.react"));

const MasterWalletManagementModal = props => {
  const [form] = Form.useForm();
  const [visible, setVisible] = React.useState(false);
  const [current, setCurrent] = React.useState(0);

  const orgName = "Reserve";

  const next = () => {
    setCurrent(current + 1);
  };

  const prev = () => {
    setCurrent(current - 1);
  };

  const onFinish = values => {
    console.log("Success:", values);
  };

  const onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

  const steps = [
    {
      title: "Home",
      content: (
        <Descriptions
          title={orgName}
          column={1}
          bordered
          extra={
            <Space>
              <Tooltip
                title={`Withdraw from ${orgName.toLowerCase()} master wallet to external address`}
              >
                <Button onClick={() => next()}>Withdraw</Button>
              </Tooltip>
            </Space>
          }
        >
          <Descriptions.Item label="Wallet Address">
            {visible ? (
              <Suspense fallback={<div>Loading QR Code...</div>}>
                <QRCode
                  style={{ margin: "1em" }}
                  size={256}
                  value={window.master_wallet_address}
                />
              </Suspense>
            ) : null}
            <Paragraph
              style={{ margin: 0 }}
              copyable={{
                text: window.master_wallet_address,
                tooltip: "Copy deposit address"
              }}
            >
              {window.master_wallet_address}{" "}
              <Tooltip title={"Deposit address QR code"}>
                <a onClick={() => setVisible(!visible)}>
                  <QrcodeOutlined />
                </a>
              </Tooltip>
            </Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="Wallet Balance">
            <Paragraph style={{ margin: 0 }}>{props.currentBalance}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="Token Name">
            <Paragraph style={{ margin: 0 }}>
              {props.activeToken.name}
            </Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="Token Created">
            <Paragraph style={{ margin: 0 }}>
              {props.activeToken.created}
            </Paragraph>
          </Descriptions.Item>
        </Descriptions>
      )
    },
    {
      title: "Withdraw",
      content: (
        <Form
          form={form}
          name="basic"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
        >
          <Form.Item
            label="Address"
            name="address"
            rules={[
              {
                required: true,
                message: "Please input your withdrawal address!"
              }
            ]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Amount"
            name="amount"
            rules={[
              {
                required: true,
                message: "Please input the amount you would like to withdraw!"
              }
            ]}
          >
            <Input type={"number"} />
          </Form.Item>
        </Form>
      )
    }
  ];

  return (
    <div>
      <Tooltip title={"Manage Master Wallet"}>
        <a onClick={props.onClick}>
          <DollarCircleOutlined translate={""} />
        </a>
      </Tooltip>
      <Modal
        title="Master Wallet Management"
        visible={props.isModalVisible}
        onOk={props.handleOk}
        onCancel={props.handleCancel}
        footer={[
          current > 0 && (
            <Button style={{ margin: "0 8px" }} onClick={() => prev()}>
              Back
            </Button>
          ),
          current === 0 && (
            <Button type="primary" onClick={props.handleOk}>
              Ok
            </Button>
          ),
          current === steps.length - 1 && (
            <Button type="primary" onClick={() => form.submit()}>
              Withdraw
            </Button>
          )
        ]}
      >
        {current === 0 ? null : (
          <Steps
            onChange={setCurrent}
            current={current}
            style={{ marginBottom: "24px" }}
          >
            {steps.map(item => (
              <Step key={item.title} title={item.title} />
            ))}
          </Steps>
        )}
        <div className="steps-content">{steps[current].content}</div>
      </Modal>
    </div>
  );
};
export default MasterWalletManagementModal;
