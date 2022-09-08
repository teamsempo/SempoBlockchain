import React from "react";
import moment from "moment";

import { connect } from "react-redux";
import { Card, Button, Space, Tag, Alert, Input } from "antd";

import { PageWrapper, WrapperDiv } from "../styledElements";

import organizationWrapper from "../organizationWrapper.jsx";
import { apiActions } from "../../genericState";
import { sempoObjects } from "../../reducers/rootReducer";
import { formatMoney, getActiveToken, toCurrency } from "../../utils";
import { DisconnectedCreditTransferList } from "../creditTransfer/CreditTransferList";
import { DisconnectedTransferAccountList } from "../transferAccount/TransferAccountList";

const { TextArea } = Input;

const mapStateToProps = (state) => ({
  bulkTransfers: state.bulkTransfers,
  activeToken: getActiveToken(state),
  transferAccounts: state.transferAccounts,
});

const mapDispatchToProps = (dispatch) => {
  return {
    loadBulkDisbursement: (path, page, per_page) =>
      dispatch(
        apiActions.load(sempoObjects.bulkTransfers, path, {
          per_page: per_page,
          page: page,
        })
      ),
    modifyBulkDisbursement: (path, body) =>
      dispatch(apiActions.modify(sempoObjects.bulkTransfers, path, body)),
  };
};

class SingleBulkDisbursementPage extends React.Component {
  navigateToUser = (accountId) => {
    window.location.assign("/users/" + accountId);
  };

  constructor(props) {
    super(props);
    this.state = {
      page: 1,
      per_page: 10,
    };
  }

  onPaginateChange = (page, pageSize) => {
    let per_page = pageSize || 10;
    this.setState({
      page,
      per_page,
    });
    this.props.loadBulkDisbursement(
      this.props.match.params.bulkId,
      page,
      per_page
    );
  };

  componentDidMount() {
    let bulkId = this.props.match.params.bulkId;
    this.props.loadBulkDisbursement(
      bulkId,
      this.state.page,
      this.state.per_page
    );
  }

  onComplete() {
    let bulkId = this.props.match.params.bulkId;
    this.props.modifyBulkDisbursement(bulkId, {
      action: "APPROVE",
      notes: this.state.notes,
    });
  }

  onReject() {
    let bulkId = this.props.match.params.bulkId;
    this.props.modifyBulkDisbursement(bulkId, {
      action: "REJECT",
      notes: this.state.notes,
    });
  }

  render() {
    let bulkId = this.props.match.params.bulkId;

    let bulkItem = this.props.bulkTransfers.byId[bulkId];
    let pagination = this.props.bulkTransfers.pagination;
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
    let completion_status = bulkItem && bulkItem.completion_status;
    let transferType = bulkItem && bulkItem.transfer_type;
    let creatorUser = bulkItem && bulkItem.creator_user;
    let approvalTimes = (bulkItem && bulkItem.approval_times) || [];
    let approvers = (bulkItem && bulkItem.approvers) || [];
    let label = bulkItem && bulkItem.label;
    let notes = bulkItem && bulkItem.notes;
    let items = pagination && pagination.items;
    let creditTransferList = (bulkItem && bulkItem.credit_transfers) || [];
    let transferAccountList = (bulkItem && bulkItem.transfer_accounts) || [];
    const approversList = approvers.map((approver, index, approversList) => {
      const spacer = index + 1 == approversList.length ? "" : ", ";
      const approvalTime = approvalTimes[index]
        ? " at " +
          moment.utc(approvalTimes[index]).local().format("YYYY-MM-DD HH:mm:ss")
        : "";
      return (
        <div>
          <a
            style={{ cursor: "pointer" }}
            onClick={() => this.navigateToUser(approver && approver.id)}
          >
            {approver && " " + approver.email}
          </a>
          {approvalTime + spacer}
        </div>
      );
    });

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
    } else if (status === "PARTIAL") {
      tag = <Tag color="#d48806">Partial</Tag>;
    } else if (status === "PENDING") {
      tag = <Tag color="#e2a963">Pending</Tag>;
    } else {
      tag = <Tag color="#f16853">Rejected</Tag>;
    }

    let completion_tag;
    if (completion_status === "COMPLETE") {
      completion_tag = <Tag color="#9bdf56">Complete</Tag>;
    } else if (completion_status === "PROCESSING") {
      completion_tag = <Tag color="#d48806">Processing</Tag>;
    } else if (completion_status === "PENDING") {
      completion_tag = <Tag color="#e2a963">Pending</Tag>;
    } else {
      completion_tag = <Tag color="#e2a963">Unknown</Tag>;
    }

    var creditTransfersById = {};
    creditTransferList.forEach((transfer) => {
      creditTransfersById[transfer.id] = transfer;
    });
    creditTransferList["byId"] = creditTransfersById;
    creditTransferList["loadStatus"] = { isRequesting: false };

    var transferAccountsById = {};
    transferAccountList.forEach((transfer) => {
      transferAccountsById[transfer.id] = transfer;
    });
    var IdList = [];
    transferAccountList.forEach((transferAccount) => {
      IdList.push(transferAccount.id);
    });
    transferAccountList["byId"] = transferAccountsById;
    transferAccountList["loadStatus"] = { isRequesting: false };
    transferAccountList["IdList"] = IdList;

    var users = [];
    transferAccountList.forEach((transferAccount) => {
      users = users.concat(transferAccount.users);
    });
    var usersByID = {};
    users.forEach((transfer) => {
      usersByID[transfer.id] = transfer;
    });
    users["byId"] = usersByID;
    users["loadStatus"] = { isRequesting: false };

    let displayList =
      completion_status === "COMPLETE" ? (
        <Card title="Included Transfers" style={{ margin: "10px" }}>
          <DisconnectedCreditTransferList
            creditTransfers={creditTransferList}
            users={users}
            paginationOptions={{
              currentPage: this.state.page,
              items: items,
              onChange: (page, perPage) => this.onPaginateChange(page, perPage),
            }}
          />
        </Card>
      ) : (
        <Card title="Included Accounts" style={{ margin: "10px" }}>
          <DisconnectedTransferAccountList
            params={this.state.params}
            searchString={this.state.searchString}
            orderedTransferAccounts={transferAccountList.IdList}
            users={users}
            transferAccounts={transferAccountList}
            actionButtons={[]}
            dataButtons={[]}
            paginationOptions={{
              currentPage: this.state.page,
              items: items,
              onChange: (page, perPage) => this.onPaginateChange(page, perPage),
            }}
          />
        </Card>
      );

    return (
      <WrapperDiv>
        <PageWrapper>
          <Card
            title={label || `Bulk Transfer ${bulkId}`}
            style={{ margin: "10px" }}
          >
            <p>
              {" "}
              <b>ID:</b> {bulkId || " "}
            </p>
            <p>
              {" "}
              <b>Created by:</b>
              <a
                style={{ cursor: "pointer" }}
                onClick={() =>
                  this.navigateToUser(creatorUser && creatorUser.id)
                }
              >
                {creatorUser && " " + creatorUser.email}
              </a>
              {" at " +
                (bulkItem &&
                  moment
                    .utc(bulkItem.created)
                    .local()
                    .format("YYYY-MM-DD HH:mm:ss")) || ""}{" "}
            </p>
            <p>
              {" "}
              <b>Reviewed By:</b>
              {approversList}
            </p>
            <p>
              {" "}
              <b>Approval status:</b> {tag}
            </p>
            <p>
              {" "}
              <b>Processing status:</b> {completion_tag}
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
            <p>
              {" "}
              <b>Errors:</b>{" "}
              {bulkItem &&
                bulkItem.errors &&
                bulkItem.errors.length > 0 &&
                bulkItem.errors.map((error) => {
                  return <Tag color="#f16853">{error}</Tag>;
                })}
            </p>
            <p>
              {" "}
              <b>Notes: </b>
              {status == "APPROVED" || status == "REJECTED" ? (
                this.state.notes || notes
              ) : (
                <TextArea
                  style={{ maxWidth: "460px" }}
                  value={this.state.notes || notes}
                  placeholder=""
                  autoSize
                  onChange={(e) => this.setState({ notes: e.target.value })}
                />
              )}
            </p>

            <Space>
              <Button
                onClick={() => this.onReject()}
                disabled={status == "APPROVED" || status == "REJECTED"}
                loading={this.props.bulkTransfers.modifyStatus.isRequesting}
              >
                Reject
              </Button>

              <Button
                onClick={() => this.onComplete()}
                disabled={status == "APPROVED" || status == "REJECTED"}
                loading={this.props.bulkTransfers.modifyStatus.isRequesting}
              >
                Approve
              </Button>
            </Space>

            {info}
          </Card>
          {displayList}
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleBulkDisbursementPage));
