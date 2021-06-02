import React, { Suspense, lazy } from "react";
import { connect, useSelector } from "react-redux";
import { sempoObjects } from "../../reducers/rootReducer";
import {
  Modal,
  Typography,
  Button,
  Tooltip,
  Descriptions,
  Space,
  Breadcrumb,
  Input,
  Form
} from "antd";
const { Paragraph } = Typography;

import { DollarCircleOutlined } from "@ant-design/icons";
import DateTime from "../dateTime";
import { apiActions } from "../../genericState";
const QRCode = lazy(() => import("qrcode.react"));

const mapStateToProps = state => {
  return {
    masterWallet: state.masterWallet
  };
};

const mapDispatchToProps = dispatch => {
  return {
    createWithdrawal: body =>
      dispatch(apiActions.create(sempoObjects.masterWallet, body))
  };
};

const MasterWalletManagementModal = props => {
  const [visible, setVisible] = React.useState(false);
  const [current, setCurrent] = React.useState(0);
  const [form] = Form.useForm();

  const activeOrganisation = useSelector(
    state => state.organisations.byId[Number(state.login.organisationId)]
  );

  const orgName = activeOrganisation && activeOrganisation.name;

  const onFinish = values => {
    const { recipient_blockchain_address, transfer_amount } = values;
    console.log("Success:", values);
    props.createWithdrawal({
      recipient_blockchain_address,
      transfer_amount: transfer_amount * 100
    });
  };

  const onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

  const next = value => {
    setCurrent(value);
  };

  const back = value => {
    setCurrent(value);
  };

  const depositQr = (
    <Descriptions.Item label="Wallet QR">
      {visible ? (
        <Suspense fallback={<div>Loading QR Code...</div>}>
          <QRCode size={256} value={window.master_wallet_address} />
        </Suspense>
      ) : null}
    </Descriptions.Item>
  );

  const depositAddress = (
    <Descriptions.Item label="Wallet Address">
      <Paragraph
        style={{ margin: 0 }}
        copyable={{
          text: window.master_wallet_address,
          tooltip: "Copy deposit address"
        }}
      >
        {window.master_wallet_address}
      </Paragraph>
    </Descriptions.Item>
  );

  const withdrawal = (
    <div>
      <Form.Item
        label="Address"
        name="recipient_blockchain_address"
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
        name="transfer_amount"
        rules={[
          {
            required: true,
            message: "Please input the amount you would like to withdraw!"
          }
        ]}
      >
        <Input type={"number"} />
      </Form.Item>
    </div>
  );

  const otherDetails = [
    {
      label: "Wallet Balance",
      value: props.currentBalance
    },
    {
      label: "Token Name",
      value: props.activeToken.name
    },
    {
      label: "Token Created",
      value: (
        <DateTime useRelativeTime={false} created={props.activeToken.created} />
      )
    }
  ];

  return (
    <Form
      form={form}
      name="basic"
      initialValues={{ remember: true }}
      onFinish={onFinish}
      onFinishFailed={onFinishFailed}
    >
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
            <Button style={{ margin: "0 8px" }} onClick={() => back(0)} key={1}>
              Back
            </Button>
          ),
          current === 0 && (
            <Button type="primary" onClick={props.handleOk} key={2}>
              Ok
            </Button>
          ),
          current === 1 && (
            <Button
              type="primary"
              onClick={() => form.submit()}
              loading={props.masterWallet.createStatus.isRequesting}
              key={3}
            >
              Withdraw
            </Button>
          )
        ]}
      >
        <Descriptions
          title={
            <Breadcrumb>
              <Breadcrumb.Item>{orgName}</Breadcrumb.Item>
              {current > 0 ? (
                <Breadcrumb.Item>
                  {current === 1 ? "Withdraw" : "Deposit"}
                </Breadcrumb.Item>
              ) : null}
            </Breadcrumb>
          }
          column={1}
          bordered
          extra={
            current === 0 ? (
              <Space>
                <Tooltip
                  title={`Withdraw from ${orgName.toLowerCase()} master wallet to external address`}
                >
                  <Button onClick={() => next(1)}>Withdraw</Button>
                </Tooltip>
                <Tooltip
                  title={`Deposit from external address to ${orgName.toLowerCase()} master wallet`}
                >
                  <Button
                    type="primary"
                    onClick={() => {
                      next(2);
                      setVisible(true);
                    }}
                  >
                    Deposit
                  </Button>
                </Tooltip>
              </Space>
            ) : (
              false
            )
          }
        >
          {current === 2 ? depositQr : null}
          {current === 0 || current === 2 ? depositAddress : null}
          {current === 0
            ? otherDetails.map((item, i) => {
                return (
                  <Descriptions.Item label={item.label} key={i}>
                    <Paragraph style={{ margin: 0 }}>{item.value}</Paragraph>
                  </Descriptions.Item>
                );
              })
            : false}
          {current === 1 ? (
            <Descriptions.Item>{withdrawal}</Descriptions.Item>
          ) : null}
        </Descriptions>
      </Modal>
    </Form>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(MasterWalletManagementModal);
