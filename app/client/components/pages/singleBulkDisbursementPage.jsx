import React from "react";
import { connect } from "react-redux";
import { Card, Button, Space, Tag, Alert } from "antd";

import { PageWrapper, WrapperDiv } from "../styledElements";

import organizationWrapper from "../organizationWrapper.jsx";
import { apiActions } from "../../genericState";
import { sempoObjects } from "../../reducers/rootReducer";
import { formatMoney, getActiveToken, toCurrency } from "../../utils";

const mapStateToProps = state => ({
  bulkTransfers: state.bulkTransfers,
  activeToken: getActiveToken(state)
});

const mapDispatchToProps = dispatch => {
  return {
    loadBulkDisbursement: path =>
      dispatch(apiActions.load(sempoObjects.bulkTransfers, path)),
    modifyBulkDisbursement: (path, body) =>
      dispatch(apiActions.modify(sempoObjects.bulkTransfers, path, body))
  };
};

class SingleBulkDisbursementPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    let bulkId = this.props.match.params.bulkId;
    this.props.loadBulkDisbursement(bulkId);
  }

  onComplete() {
    let bulkId = this.props.match.params.bulkId;

    this.props.modifyBulkDisbursement(bulkId, { action: "APPROVE" });
  }

  onReject() {
    let bulkId = this.props.match.params.bulkId;

    this.props.modifyBulkDisbursement(bulkId, { action: "REJECT" });
  }

  render() {
    let bulkId = this.props.match.params.bulkId;

    let bulkItem = this.props.bulkTransfers.byId[bulkId];

    let totalAmount;
    if (bulkItem && bulkItem.total_disbursement_amount) {
      totalAmount = formatMoney(
        toCurrency(bulkItem.total_disbursement_amount),
        undefined,
        undefined,
        undefined,
        this.props.activeToken.symbol
      );
    }

    let individualAmount;
    if (bulkItem && bulkItem.disbursement_amount) {
      individualAmount = formatMoney(
        bulkItem.disbursement_amount / 100,
        undefined,
        undefined,
        undefined,
        this.props.activeToken.symbol
      );
    }

    let status = bulkItem && bulkItem.state;
    let transferType = bulkItem && bulkItem.transfer_type;
    let createdBy = bulkItem && bulkItem.creator_email;

    let tag;
    let info;
    if (status === "APPROVED") {
      tag = <Tag color="#9bdf56">Approved</Tag>;
      info = (
        <div style={{ maxWidth: "700px", marginTop: "20px" }}>
          <Alert
            message="If there are many disbursements, it can take a while for all of them to appear in the transfers list."
            type="info"
            showIcon
          />
        </div>
      );
    } else if (status === "PENDING") {
      tag = <Tag color="#e2a963">Pending</Tag>;
    } else {
      tag = <Tag color="#f16853">Rejected</Tag>;
    }

    return (
      <WrapperDiv>
        <PageWrapper>
          <Card title={`Bulk Transfer ${bulkId}`} style={{ margin: "10px" }}>
            <p>
              {" "}
              <b>Created by:</b> {createdBy || " "}
            </p>
            <p>
              {" "}
              <b>Current status:</b> {tag}
            </p>
            <p>
              {" "}
              <b>Transfer Type:</b> {transferType || " "}
            </p>
            <p>
              {" "}
              <b>Number of recipients:</b>{" "}
              {(bulkItem && bulkItem.recipient_count) || ""}{" "}
            </p>
            <p>
              {" "}
              <b>Amount per recipeint:</b> {individualAmount || ""}{" "}
            </p>
            <p>
              {" "}
              <b>Total amount transferred:</b> {totalAmount || ""}{" "}
            </p>

            <Space>
              <Button
                onClick={() => this.onReject()}
                disabled={status !== "PENDING"}
                loading={this.props.bulkTransfers.modifyStatus.isRequesting}
              >
                Reject
              </Button>

              <Button
                onClick={() => this.onComplete()}
                disabled={status !== "PENDING"}
                loading={this.props.bulkTransfers.modifyStatus.isRequesting}
              >
                Approve
              </Button>
            </Space>

            {info}
          </Card>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleBulkDisbursementPage));