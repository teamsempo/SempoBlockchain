import React from "react";
import moment from "moment";
import { connect } from "react-redux";
import { Card, Empty, Statistic, Tag, Descriptions, Button, Space } from "antd";
import { DollarOutlined } from "@ant-design/icons";

import {
  LoadCreditTransferAction,
  ModifyCreditTransferAction,
} from "../../reducers/creditTransfer/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import {
  getActiveToken,
  replaceUnderscores,
  toCurrency,
  toTitleCase,
} from "../../utils";

const mapStateToProps = (state, ownProps) => {
  return {
    activeToken: getActiveToken(state),
    creditTransfer: state.creditTransfers.byId[ownProps.creditTransferId],
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadCreditTransferList: (path) =>
      dispatch(LoadCreditTransferAction.loadCreditTransferListRequest(path)),
    modifyTransferRequest: (payload) =>
      dispatch(ModifyCreditTransferAction.modifyTransferRequest(payload)),
  };
};

class SingleCreditTransfer extends React.Component {
  handleClick(action) {
    this.props.modifyTransferRequest({
      body: { action: action },
      path: this.props.creditTransferId,
    });
  }
  navigateToUser = (accountId) => {
    window.location.assign("/users/" + accountId);
  };
  navigateToTransferAccount = (accountId) => {
    window.location.assign("/accounts/" + accountId);
  };

  render() {
    const { creditTransfer, activeToken } = this.props;
    const symbol = activeToken && activeToken.symbol;

    if (creditTransfer) {
      // Transfer Metadata
      const blockchainId = creditTransfer.blockchain_task_uuid;
      const blockchainStatus = creditTransfer.blockchain_status;

      const transferUsages = creditTransfer.transfer_uses.join(", ");

      const transferStatus = creditTransfer.transfer_status;
      const transferMode = creditTransfer.transfer_mode;
      const resolutionMessage = creditTransfer.resolution_message;

      const createDate = moment
        .utc(creditTransfer.created)
        .local()
        .format("YYYY-MM-DD HH:mm:ss");
      const resolveDate = moment
        .utc(creditTransfer.resolved)
        .local()
        .format("YYYY-MM-DD HH:mm:ss");

      const lat = creditTransfer.lat;
      const lng = creditTransfer.lng;
      const coords = lat && lng ? lat + ", " + lng : "";
      // Sender Info
      const senderUserID = creditTransfer.sender_user;
      const recipientUserID = creditTransfer.recipient_user;
      // Recipient Info
      const senderTransferAccountID = creditTransfer.sender_transfer_account;
      const recipientTransferAccountID =
        creditTransfer.recipient_transfer_account;

      const transferCardSerialNumber =
        creditTransfer.transfer_card_public_serial_number || "";

      const actionsDisabled =
        creditTransfer.transfer_status !== "PENDING" &&
        creditTransfer.transfer_status !== "PARTIAL";
      const tagColor =
        creditTransfer.transfer_status === "COMPLETE"
          ? "green"
          : creditTransfer.transfer_status === "REJECTED"
          ? "red"
          : "orange";
      const tag = (
        <Tag color={tagColor} style={{ margin: "auto 1em" }}>
          {creditTransfer.transfer_status}
        </Tag>
      );

      return (
        <Card
          style={{ marginTop: "16px" }}
          title={
            <Statistic
              title={
                <p>
                  <DollarOutlined /> {creditTransfer.transfer_type}
                </p>
              }
              value={toCurrency(creditTransfer.transfer_amount)}
              suffix={
                <span style={{ display: "inline-flex" }}>
                  {symbol} {tag}
                </span>
              }
            />
          }
          extra={
            <Space>
              <Button
                disabled={actionsDisabled}
                type="primary"
                onClick={() => this.handleClick("COMPLETE")}
              >
                Complete
              </Button>
              <Button
                disabled={actionsDisabled}
                onClick={() => this.handleClick("REJECT")}
              >
                Reject
              </Button>
            </Space>
          }
        >
          <Descriptions title={"Transfer Information"}>
            <Descriptions.Item label={"Transfer Status"}>
              {transferStatus}
            </Descriptions.Item>
            <Descriptions.Item label={"Transfer Mode"}>
              {transferMode}
            </Descriptions.Item>
            <Descriptions.Item label={"Blockchain Status"}>
              {blockchainStatus}
            </Descriptions.Item>
            <Descriptions.Item label={"Blockchain UUID"}>
              {blockchainId}
            </Descriptions.Item>
            <Descriptions.Item label={"Resolution Message"}>
              {resolutionMessage}
            <Descriptions.Item label={"Transfer Uses"}>
              {transferUsages}
            </Descriptions.Item>
          </Descriptions>

          <Descriptions title={"Transfer Metadata"}>
            <Descriptions.Item label={"Date Created"}>
              {createDate}
            </Descriptions.Item>
            <Descriptions.Item label={"Date Resolved"}>
              {resolveDate}
            </Descriptions.Item>
            <Descriptions.Item label={"Coordinates"}>
              {coords}
            </Descriptions.Item>
          </Descriptions>

          <Descriptions title={"Sender Information"}>
            <Descriptions.Item label={"Sender Transfer Account"}>
              <a
                style={{ cursor: "pointer" }}
                onClick={() =>
                  this.navigateToTransferAccount(senderTransferAccountID)
                }
              >
                {senderTransferAccountID}
              </a>
            </Descriptions.Item>
            <Descriptions.Item label={"Sender User"}>
              <a
                style={{ cursor: "pointer" }}
                onClick={() => this.navigateToUser(senderUserID)}
              >
                {senderUserID}
              </a>
            </Descriptions.Item>
            <Descriptions.Item label={"Transfer Card Serial Number"}>
              {transferCardSerialNumber}
            </Descriptions.Item>
          </Descriptions>

          <Descriptions title={"Recipient Information"}>
            <Descriptions.Item label={"Recipient Transfer Account"}>
              <a
                style={{ cursor: "pointer" }}
                onClick={() =>
                  this.navigateToTransferAccount(recipientTransferAccountID)
                }
              >
                {recipientTransferAccountID}
              </a>
            </Descriptions.Item>
            <Descriptions.Item label={"Recipient User"}>
              <a
                style={{ cursor: "pointer" }}
                onClick={() => this.navigateToUser(recipientUserID)}
              >
                {recipientUserID}
              </a>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      );
    } else {
      return <Empty />;
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleCreditTransfer));
