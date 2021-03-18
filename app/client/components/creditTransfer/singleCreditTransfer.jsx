import React from "react";
import { connect } from "react-redux";
import { Card, Empty, Statistic, Tag, Descriptions, Button, Space } from "antd";
import { DollarOutlined } from "@ant-design/icons";

import {
  LoadCreditTransferAction,
  ModifyCreditTransferAction
} from "../../reducers/creditTransfer/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import {
  getActiveToken,
  replaceUnderscores,
  toCurrency,
  toTitleCase
} from "../../utils";

const mapStateToProps = (state, ownProps) => {
  return {
    activeToken: getActiveToken(state),
    creditTransfer: state.creditTransfers.byId[ownProps.creditTransferId]
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadCreditTransferList: path =>
      dispatch(LoadCreditTransferAction.loadCreditTransferListRequest(path)),
    modifyTransferRequest: payload =>
      dispatch(ModifyCreditTransferAction.modifyTransferRequest(payload))
  };
};

class SingleCreditTransfer extends React.Component {
  handleClick(action) {
    this.props.modifyTransferRequest({
      body: { action: action },
      path: this.props.creditTransferId
    });
  }

  render() {
    const { creditTransfer, activeToken } = this.props;
    const symbol = activeToken && activeToken.symbol;

    if (creditTransfer) {
      const actionsDisabled = creditTransfer.transfer_status !== "PENDING";
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

      const timeline = Object.keys(creditTransfer).filter(
        value =>
          value.includes("created") ||
          value.includes("updated") ||
          value.includes("resolved")
      );
      console.log("timeline", timeline);

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
          <Descriptions title={"Credit Transfer Info"}>
            {Object.keys(creditTransfer).map(key => (
              <Descriptions.Item label={toTitleCase(replaceUnderscores(key))}>
                {creditTransfer[key]}
              </Descriptions.Item>
            ))}
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
