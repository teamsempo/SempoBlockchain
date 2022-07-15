import React from "react";
import moment from "moment";

import { connect } from "react-redux";
import { Card, Button, Space, Tag, Alert, Input } from "antd";

import { PageWrapper, WrapperDiv } from "../styledElements";

import organizationWrapper from "../organizationWrapper.jsx";
import { apiActions } from "../../genericState";
import { sempoObjects } from "../../reducers/rootReducer";
import { formatMoney, getActiveToken, toCurrency } from "../../utils";
import QueryConstructor from "../filterModule/queryConstructor";
import TransferAccountList from "../transferAccount/TransferAccountList";
const { TextArea } = Input;

const mapStateToProps = (state) => ({
  bulkTransfers: state.bulkTransfers,
  activeToken: getActiveToken(state),
  transferAccounts: state.transferAccounts,
});

const mapDispatchToProps = (dispatch) => {
  return {
    loadBulkDisbursement: (path) =>
      dispatch(apiActions.load(sempoObjects.bulkTransfers, path)),
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
  };

  componentDidMount() {
    let bulkId = this.props.match.params.bulkId;
    this.props.loadBulkDisbursement(bulkId);
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
          <Card
            title="Included Accounts (not editable)"
            style={{ margin: "10px" }}
          >
            <QueryConstructor
              onQueryChange={(query) => {}}
              filterObject="user"
              providedParams={bulkItem && bulkItem.search_filter_params}
              providedSearchString={bulkItem && bulkItem.search_string}
              pagination={{
                page: this.state.page,
                per_page: this.state.per_page,
              }}
              disabled={true}
            />
            <TransferAccountList
              orderedTransferAccounts={this.props.transferAccounts.IdList}
              disabled={true}
              actionButtons={[]}
              dataButtons={[]}
              noneSelectedbuttons={[]}
              onSelectChange={(s, u, a) => {}}
              providedSelectedRowKeys={bulkItem && bulkItem.include_accounts}
              providedUnselectedRowKeys={bulkItem && bulkItem.exclude_accounts}
              paginationOptions={{
                currentPage: this.state.page,
                items: this.props.transferAccounts.pagination.items,
                onChange: (page, perPage) =>
                  this.onPaginateChange(page, perPage),
              }}
            />
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
