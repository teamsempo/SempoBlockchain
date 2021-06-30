import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import ReactTable from "react-table";
import { Link } from "react-router-dom";

import { TopRow, StyledSelect } from "../styledElements.js";

import { ModifyCreditTransferAction } from "../../reducers/creditTransfer/actions";

import LoadingSpinner from "../loadingSpinner.jsx";
import DateTime from "../dateTime.tsx";
import AsyncButton from "../AsyncButton.jsx";
import { formatMoney } from "../../utils";
import { ModuleBox } from "../styledElements";

const mapStateToProps = state => {
  return {
    login: state.login,
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
    users: state.users,
    tokens: state.tokens
  };
};

const mapDispatchToProps = dispatch => {
  return {
    modifyTransferRequest: payload =>
      dispatch(ModifyCreditTransferAction.modifyTransferRequest(payload))
  };
};

class CreditTransferList extends React.Component {
  // ---- INFO ----
  // CreditTransferList accepts;
  // credit_transfer_ids
  //    + array of credit transfer ids (only filterable by payment type)
  // or credit_transfer_list (item_list)
  //    + array of credit transfer objects
  //    + filterable and searchable via creditTransferListWithFilterWrapper
  constructor() {
    super();
    this.state = {
      action: false,
      user_id: null,
      transfer_type: "ALL",
      credit_transfer_ids: {},
      allCheckedCreditTransfers: false,
      isLoading: true
    };
    this.checkAllCreditTransfers = this.checkAllCreditTransfers.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.toggleSelectedCreditTransfer = this.toggleSelectedCreditTransfer.bind(
      this
    );
    this.onNext = this.onNext.bind(this);
  }

  componentDidMount() {
    // accepts both credit_transfer_ids and credit_transfer_list (item_list)
    let creditTransferIds = this.props.credit_transfer_ids;
    let creditTransferList = this.props.item_list;

    // handles credit transfer ids array
    if (creditTransferIds) {
      this.sortCreditTransfers(creditTransferIds);
    }

    // handles credit transfer list array
    if (creditTransferList) {
      creditTransferList.map(i => {
        this.setState(prevState => ({
          credit_transfer_ids: {
            ...prevState.credit_transfer_ids,
            [i.id]: false
          }
        }));
      });
    }

    this.setState({ isLoading: false });
  }

  componentDidUpdate(prevProps) {
    let { credit_transfer_ids, item_list } = this.props;

    // handles credit_transfer_ids array
    if (credit_transfer_ids !== prevProps.credit_transfer_ids) {
      this.setState({ credit_transfer_ids: {} });
      this.sortCreditTransfers(credit_transfer_ids);
    }

    // handles credit_transfer_list array
    if (item_list !== prevProps.item_list) {
      this.setState({ credit_transfer_ids: {} });

      item_list.map(i => {
        this.setState(prevState => ({
          credit_transfer_ids: {
            ...prevState.credit_transfer_ids,
            [i.id]: false
          },
          isLoading: false
        }));
      });
    }
  }

  // handles credit transfer ids array
  sortCreditTransfers = creditTransferIds => {
    creditTransferIds.map(i => {
      this.setState(prevState => ({
        credit_transfer_ids: {
          ...prevState.credit_transfer_ids,
          [i]: false
        }
      }));
      this.setState({ isLoading: false });
    });
  };

  get_selected_ids_array(selected) {
    Object.filter = (obj, predicate) =>
      Object.keys(obj)
        .filter(key => predicate(obj[key]))
        .reduce((res, key) => ((res[key] = obj[key]), res), {});

    return Object.keys(Object.filter(selected, selected => selected === true));
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  toggleSelectedCreditTransfer(id) {
    const value = !this.state.credit_transfer_ids[id];

    this.setState(prevState => ({
      credit_transfer_ids: {
        ...prevState.credit_transfer_ids,
        [id]: value
      },
      allChecked: false
    }));
  }

  onNext() {
    this.get_selected_ids_array(this.state.credit_transfer_ids).map(id =>
      this.props.modifyTransferRequest({
        body: { action: this.state.action },
        path: id
      })
    );
  }

  displaySelect(id) {
    if (this.state.credit_transfer_ids[id] !== null) {
      return (
        <input
          name={id}
          type="checkbox"
          checked={this.state.credit_transfer_ids[id]}
          onChange={() => this.toggleSelectedCreditTransfer(id)}
        />
      );
    }
  }

  checkAllCreditTransfers(filteredData) {
    if (this.state.allCheckedCreditTransfers) {
      // UNCHECK
      var value = false;
    } else {
      // CHECK ALL
      value = true;
    }

    filteredData.map(i => {
      this.setState(prevState => ({
        credit_transfer_ids: {
          ...prevState.credit_transfer_ids,
          [i.id]: value
        },
        allCheckedCreditTransfers: value
      }));
    });
  }

  navigateToAccount = accountId => {
    window.location.assign("/accounts/" + accountId);
  };

  _customSender(creditTransfer) {
    let transferAccounts = this.props.transferAccounts.byId;
    let senderTransferAccount =
      transferAccounts[creditTransfer.sender_transfer_account_id];

    let sender =
      creditTransfer.sender_user &&
      this.props.users.byId[creditTransfer.sender_user];
    let firstName = sender && sender.first_name;
    let lastName = sender && sender.last_name;
    let email = creditTransfer.authorising_user_email;
    let blockchainAddress =
      senderTransferAccount && senderTransferAccount.blockchain_address;

    if (this.props.login.adminTier === "view") {
      let viewTransferAccountName =
        senderTransferAccount && senderTransferAccount.is_vendor
          ? "Vendor "
          : window.BENEFICIARY_TERM + " ";
      return (
        <a
          style={{ cursor: "pointer" }}
          onClick={() =>
            this.navigateToAccount(creditTransfer.sender_transfer_account_id)
          }
        >
          {viewTransferAccountName + blockchainAddress}
        </a>
      );
    } else if (sender && (firstName || lastName)) {
      return (
        <a
          style={{ cursor: "pointer" }}
          onClick={() =>
            this.navigateToAccount(creditTransfer.sender_transfer_account_id)
          }
        >
          {(firstName === null ? "" : firstName) +
            " " +
            (lastName === null ? "" : lastName)}
        </a>
      );
    } else if (creditTransfer.transfer_type === "DISBURSEMENT" && email) {
      return <div style={{ color: "#96DADC" }}> {email} </div>;
    } else {
      return "-";
    }
  }

  _customRecipient(creditTransfer) {
    let transferAccounts = this.props.transferAccounts.byId;
    let recipientTransferAccount =
      transferAccounts[creditTransfer.recipient_transfer_account_id];

    let recipient =
      creditTransfer.recipient_user &&
      this.props.users.byId[creditTransfer.recipient_user];
    let firstName = recipient && recipient.first_name;
    let lastName = recipient && recipient.last_name;
    let email = creditTransfer.authorising_user_email;
    let blockchainAddress =
      recipientTransferAccount && recipientTransferAccount.blockchain_address;

    if (this.props.login.adminTier === "view") {
      let viewTransferAccountName =
        recipientTransferAccount && recipientTransferAccount.is_vendor
          ? "Vendor "
          : window.BENEFICIARY_TERM + " ";
      return (
        <a
          style={{ cursor: "pointer" }}
          onClick={() =>
            this.navigateToAccount(creditTransfer.recipient_transfer_account_id)
          }
        >
          {viewTransferAccountName + blockchainAddress}
        </a>
      );
    } else if (recipient && (firstName || lastName)) {
      return (
        <a
          style={{ cursor: "pointer" }}
          onClick={() =>
            this.navigateToAccount(creditTransfer.recipient_transfer_account_id)
          }
        >
          {(firstName === null ? "" : firstName) +
            " " +
            (lastName === null ? "" : lastName)}
        </a>
      );
    } else if (creditTransfer.transfer_type === "RECLAMATION" && email) {
      return <div style={{ color: "#96DADC" }}> {email} </div>;
    } else {
      return "-";
    }
  }

  render() {
    const { creditTransfers, transfer_account_id } = this.props;
    // const loadingStatus = creditTransfers.loadStatus.isRequesting;

    let creditTransferList = Object.keys(this.state.credit_transfer_ids)
      .filter(id => typeof this.props.creditTransfers.byId[id] !== "undefined")
      .map(id => this.props.creditTransfers.byId[id])
      .sort((a, b) => b.id - a.id);

    let rowValues = Object.values(this.state.credit_transfer_ids);
    let numberSelected =
      typeof rowValues !== "undefined"
        ? rowValues.filter(Boolean).length
        : null;
    let isSelected = numberSelected > 0;

    let showNext = numberSelected === 0 || this.props.action === "select";

    if (this.state.transfer_type !== "ALL") {
      var filteredData = creditTransferList.filter(
        creditTransfer =>
          creditTransfer.transfer_type === this.state.transfer_type
      );
    } else {
      filteredData = creditTransferList;
    }

    if (isSelected) {
      var topBarContent = (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            width: "100%"
          }}
        >
          <p style={{ margin: "1em" }}>{numberSelected} selected</p>
          {this.props.login.adminTier !== "view" ? (
            <div style={{ margin: "1em" }}>
              <AsyncButton
                onClick={this.onNext}
                buttonStyle={{
                  display: showNext ? "none" : "inline-flex",
                  fontWeight: "400",
                  margin: "0em 1em",
                  lineHeight: "25px",
                  height: "25px"
                }}
                isLoading={this.props.isApproving}
                buttonText={<span>NEXT</span>}
                label={"Next action"}
              />
              <StyledSelect
                style={{
                  fontWeight: "400",
                  margin: "0",
                  lineHeight: "25px",
                  height: "25px"
                }}
                name="action"
                defaultValue="select"
                onChange={this.handleChange}
              >
                <option name="action" disabled value="select">
                  -- SELECT --
                </option>
                <option name="action" value="COMPLETE">
                  COMPLETE
                </option>
                <option name="action" value="REJECT">
                  REJECT
                </option>
              </StyledSelect>
            </div>
          ) : null}
        </div>
      );
    } else {
      topBarContent = (
        <StyledSelect
          style={{
            fontWeight: "400",
            margin: "1em",
            lineHeight: "25px",
            height: "25px"
          }}
          name="transfer_type"
          value={this.props.transfer_type}
          onChange={this.handleChange}
        >
          <option name="transfer_type" value="ALL">
            ALL TRANSFERS
          </option>
          <option name="transfer_type" value="PAYMENT">
            PAYMENTS
          </option>
          <option name="transfer_type" value="EXCHANGE">
            EXCHANGE
          </option>
          <option name="transfer_type" value="DISBURSEMENT">
            DISBURSEMENTS
          </option>
          <option name="transfer_type" value="RECLAMATION">
            RECLAMATION
          </option>
          <option name="transfer_type" value="WITHDRAWAL">
            WITHDRAWAL
          </option>
          <option name="transfer_type" value="DEPOSIT">
            DEPOSIT
          </option>
          <option name="transfer_type" value="FEE">
            FEE
          </option>
        </StyledSelect>
      );
    }

    if (
      this.props.creditTransfers.newLoadStatus.isRequesting ||
      this.props.transferAccounts.loadStatus.isRequesting
    ) {
      return (
        <div
          style={{ display: "flex", justifyContent: "center", margin: "1em" }}
        >
          <LoadingSpinner />
        </div>
      );
    }

    return (
      <Wrapper>
        <ModuleBox style={{ width: "calc(100% - 2em)" }}>
          <TopRow>{topBarContent}</TopRow>
          <ReactTable
            columns={[
              {
                Header: "Id",
                accessor: "id",
                headerClassName: "react-table-header",
                width: 60
              },
              {
                Header: "Type",
                accessor: "transfer_type",
                headerClassName: "react-table-header",
                className: "react-table-first-cell",
                Cell: cellInfo => {
                  const transferId = cellInfo.original.id;
                  const customRoutes = transfer_account_id
                    ? [
                        { path: "", breadcrumbName: "Home" },
                        { path: "accounts/", breadcrumbName: "Accounts" },
                        {
                          path: `accounts/${transfer_account_id}`,
                          breadcrumbName: `Transfer Account ${transfer_account_id}`
                        },
                        {
                          path: `transfers/${transferId}`,
                          breadcrumbName: `Transfer ${transferId}`
                        }
                      ]
                    : undefined;
                  return (
                    <Link
                      to={{
                        pathname: "/transfers/" + transferId,
                        state: { customRoutes }
                      }}
                      style={{
                        textDecoration: "underline",
                        color: "#000000a6"
                      }}
                    >
                      {cellInfo.original.transfer_type}
                    </Link>
                  );
                }
              },
              {
                Header: "Created",
                accessor: "created",
                headerClassName: "react-table-header",
                Cell: cellInfo => <DateTime created={cellInfo.value} />
              },
              {
                Header: "Amount",
                accessor: "transfer_amount",
                headerClassName: "react-table-header",
                Cell: cellInfo => {
                  let currency =
                    cellInfo.original.token &&
                    this.props.tokens.byId[cellInfo.original.token] &&
                    this.props.tokens.byId[cellInfo.original.token].symbol;
                  const money = formatMoney(
                    cellInfo.value / 100,
                    undefined,
                    undefined,
                    undefined,
                    currency
                  );
                  return <p style={{ margin: 0 }}>{money}</p>;
                }
              },
              {
                Header: "Sender",
                id: "senderUser",
                accessor: creditTransfer => this._customSender(creditTransfer),
                headerClassName: "react-table-header"
              },
              {
                Header: "Recipient",
                id: "recipientUser",
                accessor: creditTransfer =>
                  this._customRecipient(creditTransfer),
                headerClassName: "react-table-header"
              },
              {
                Header: "Approval",
                accessor: "transfer_status",
                headerClassName: "react-table-header",
                Cell: cellInfo => {
                  if (cellInfo.value === "COMPLETE") {
                    var colour = "#9BDF56";
                  } else if (cellInfo.value === "PENDING") {
                    colour = "#F5A623";
                  } else if (cellInfo.value === "PARTIAL") {
                    colour = "#d48806";
                  } else if (cellInfo.value === "REJECTED") {
                    colour = "#F16853";
                  } else {
                    colour = "#c6c6c6";
                  }
                  return (
                    <div
                      style={{
                        height: "100%",
                        display: "flex",
                        alignItems: "center"
                      }}
                    >
                      <Status style={{ backgroundColor: colour }}>
                        {cellInfo.value}
                      </Status>
                    </div>
                  );
                }
              },
              {
                Header: "Blockchain",
                id: "blockchain_status",
                accessor: creditTransfer => {
                  try {
                    var task =
                      creditTransfer.blockchain_status_breakdown.transfer ||
                      creditTransfer.blockchain_status_breakdown.disbursement;
                  } catch (e) {
                    task = {};
                  }
                  return {
                    status: creditTransfer.blockchain_status,
                    hash: task.hash
                  };
                },
                headerClassName: "react-table-header",
                Cell: cellInfo => {
                  let { status, hash } = cellInfo.value;

                  if (status === "COMPLETE") {
                    var colour = "#9BDF56";
                  } else if (status === "PENDING") {
                    colour = "#F5A623";
                  } else if (cellInfo.value === "PARTIAL") {
                    colour = "#d48806";
                  } else if (status === "UNSTARTED") {
                    colour = "#F16853";
                  } else if (status === "ERROR") {
                    colour = "#F16853";
                  } else {
                    colour = "#c6c6c6";
                  }

                  if (hash) {
                    var tracker_link = window.ETH_EXPLORER_URL + "/tx/" + hash;
                  } else {
                    tracker_link = null;
                  }
                  return (
                    <div
                      style={{
                        height: "100%",
                        display: "flex",
                        alignItems: "center"
                      }}
                    >
                      <Status
                        style={{ backgroundColor: colour }}
                        href={tracker_link}
                        target="_blank"
                      >
                        {status}
                      </Status>
                    </div>
                  );
                }
              },
              {
                Header: () => (
                  <input
                    type="checkbox"
                    checked={this.state.allCheckedCreditTransfers}
                    onChange={() => this.checkAllCreditTransfers(filteredData)}
                  />
                ),
                accessor: "id",
                headerClassName: "react-table-header",
                width: 60,
                sortable: false,
                Cell: cellInfo => this.displaySelect(cellInfo.value)
              }
            ]}
            data={filteredData}
            //loading={loadingStatus} // Display the loading overlay when we need it
            pageSize={20}
            sortable={true}
            showPagination={true}
            showPageSizeOptions={false}
            className="react-table"
            resizable={false}
            getTdProps={(state, rowInfo) => {
              return {
                onClick: (e, handleOriginal) => {
                  if (rowInfo) {
                    this.toggleSelectedCreditTransfer(rowInfo.row.id);
                  }
                  if (handleOriginal) {
                    handleOriginal();
                  }
                }
              };
            }}
          />
        </ModuleBox>
      </Wrapper>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(CreditTransferList);

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const Status = styled.a`
  color: #fff;
  padding: 0.2em 1em;
  margin: 0;
  font-weight: 500;
  border-radius: 20px;
  text-transform: uppercase;
  font-size: 12px;
  width: 90px;
  text-align: center;
`;
