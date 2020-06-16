import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import ReactTable from "react-table";
import { browserHistory } from "../../createStore.js";

import {
  ModuleBox,
  TopRow,
  StyledButton,
  StyledSelect,
  Wrapper
} from "../styledElements.js";

import LoadingSpinner from "../loadingSpinner.jsx";
import DateTime from "../dateTime.jsx";
import NewTransferManager from "../management/newTransferManager.jsx";

import { formatMoney } from "../../utils";
import {
  editTransferAccount,
  setSelected,
  loadTransferAccounts
} from "../../reducers/transferAccountReducer";
import { TransferAccountTypes } from "../transferAccount/types";

const mapStateToProps = state => {
  return {
    login: state.login,
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers
  };
};

const mapDispatchToProps = dispatch => {
  return {
    editTransferAccountRequest: body => dispatch(editTransferAccount({ body })),
    setSelected: selected => dispatch(setSelected(selected)),
    loadTransferAccounts: (query, path) =>
      dispatch(loadTransferAccounts({ query, path }))
  };
};

class TransferAccountList extends React.Component {
  // ---- INFO ----
  // TransferAccountList accepts;
  // transfer_account_list (pass in as item_list)
  //    + array of transfer account objects
  //    + filterable and searchable via SearchBoxWithFilter
  constructor() {
    super();
    this.state = {
      data: [],
      loading: true,
      user_id: null,
      idSelectedStatus: {},
      allCheckedTransferAccounts: false,
      newTransfer: false,
      account_type: "ALL"
    };
    this.handleChange = this.handleChange.bind(this);
    this.checkAllTransferAccounts = this.checkAllTransferAccounts.bind(this);
    this.toggleSelectedTransferAccount = this.toggleSelectedTransferAccount.bind(
      this
    );
    this.onNewTransfer = this.onNewTransfer.bind(this);
    this.approveSelected = this.approveSelected.bind(this);
  }

  componentWillUnmount() {
    this.props.setSelected(
      this.get_selected_ids_array(this.state.idSelectedStatus)
    );
  }

  componentDidUpdate(newProps) {
    if (
      this.props.creditTransfers.createStatus.success !==
      newProps.creditTransfers.createStatus.success
    ) {
      this.setState({ newTransfer: false });
    }
  }

  get_selected_ids_array(statusDict) {
    return Object.keys(statusDict).filter(id => statusDict[id] === true);
  }

  toggleSelectedTransferAccount(id) {
    const value = !(this.state.idSelectedStatus[id] || false);

    this.setState(prevState => ({
      idSelectedStatus: {
        ...prevState.idSelectedStatus,
        [id]: value
      },
      allCheckedTransferAccounts: false
    }));
  }

  displaySelect(id) {
    let checked = this.state.idSelectedStatus[id] || false;

    return (
      <input
        name={id}
        type="checkbox"
        checked={checked}
        onChange={() => this.toggleSelectedTransferAccount(id)}
      />
    );
  }

  checkAllTransferAccounts(filteredData) {
    if (this.state.allCheckedTransferAccounts) {
      // UNCHECK ALL
      this.setState({
        idSelectedStatus: {},
        allCheckedTransferAccounts: false
      });
    } else {
      // CHECK ALL FILTERED
      let checked = {};
      filteredData.map(ta => {
        checked[ta.id] = true;
      });
      this.setState({
        allCheckedTransferAccounts: true,
        idSelectedStatus: checked
      });
    }
  }

  onNewTransfer() {
    this.setState(prevState => ({
      newTransfer: !prevState.newTransfer
    }));
  }

  approveSelected() {
    let approve = true;
    let transfer_account_id_list = this.get_selected_ids_array(
      this.state.idSelectedStatus
    );

    this.props.editTransferAccountRequest({
      transfer_account_id_list,
      approve
    });
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  _customName(transferAccount) {
    if (
      this.props.login.adminTier === "view" &&
      typeof transferAccount.blockchain_address !== "undefined"
    ) {
      return transferAccount.blockchain_address;
    }
    return (
      (transferAccount.first_name === null ? "" : transferAccount.first_name) +
      " " +
      (transferAccount.last_name === null ? "" : transferAccount.last_name)
    );
  }

  _customIcon(transferAccount) {
    let url = "/static/media/user.svg";
    if (transferAccount.is_beneficiary) {
      url = "/static/media/user.svg";
    } else if (transferAccount.is_vendor) {
      url = "/static/media/store.svg";
    } else if (transferAccount.is_groupaccount) {
      url = "/static/media/groupaccount.svg";
    } else if (transferAccount.is_tokenagent) {
      url = "/static/media/tokenagent.svg";
    }
    return <UserSVG src={url} />;
  }

  render() {
    const { account_type } = this.state;
    const loadingStatus = this.props.transferAccounts.loadStatus.isRequesting;
    let accountTypes = Object.keys(TransferAccountTypes);
    accountTypes.push("ALL"); // filter should have all option

    var filteredData =
      this.props.item_list !== undefined ? this.props.item_list : null;

    if (account_type === TransferAccountTypes.USER) {
      filteredData = filteredData.filter(account => account.is_beneficiary);
    } else if (
      account_type === TransferAccountTypes.VENDOR ||
      account_type === TransferAccountTypes.CASHIER
    ) {
      filteredData = filteredData.filter(account => account.is_vendor);
    } else if (account_type === TransferAccountTypes.TOKENAGENT) {
      filteredData = filteredData.filter(account => account.is_tokenagent);
    } else if (account_type === TransferAccountTypes.GROUPACCOUNT) {
      filteredData = filteredData.filter(account => account.is_groupaccount);
    }

    let rowValues = Object.values(this.state.idSelectedStatus);
    let numberSelected = rowValues.filter(Boolean).length;
    let isSelected = numberSelected > 0;

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
            <div style={{ margin: "1em 0", display: "flex" }}>
              <StyledButton
                onClick={this.onNewTransfer}
                style={{
                  display: this.state.newTransfer ? "none" : "flex",
                  fontWeight: "400",
                  margin: "0em 1em",
                  lineHeight: "25px",
                  height: "25px"
                }}
              >
                NEW TRANSFER
              </StyledButton>
              <StyledButton
                onClick={this.approveSelected}
                style={{
                  display: this.state.newTransfer ? "none" : "flex",
                  fontWeight: "400",
                  margin: "0em 1em 0 0",
                  lineHeight: "25px",
                  height: "25px"
                }}
              >
                APPROVE
              </StyledButton>
              <UploadButtonWrapper style={{ marginRight: 0, marginLeft: 0 }}>
                <StyledButton
                  onClick={() => browserHistory.push("/export")}
                  style={{
                    fontWeight: "400",
                    margin: "0em 1em 0 0",
                    lineHeight: "25px",
                    height: "25px"
                  }}
                >
                  Export
                </StyledButton>
              </UploadButtonWrapper>
            </div>
          ) : null}
        </div>
      );
    } else {
      topBarContent = (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            width: "100%"
          }}
        >
          <StyledSelect
            style={{
              fontWeight: "400",
              margin: "1em",
              lineHeight: "25px",
              height: "25px"
            }}
            name="account_type"
            value={this.state.account_type}
            onChange={this.handleChange}
          >
            {accountTypes.map((accountType, index) => {
              return (
                <option key={index} name="account_type" value={accountType}>
                  {accountType}
                </option>
              );
            })}
          </StyledSelect>

          {this.props.login.adminTier !== "view" ? (
            <div style={{ display: "flex", flexDirection: "row" }}>
              <UploadButtonWrapper style={{ marginRight: 0, marginLeft: 0 }}>
                <StyledButton
                  onClick={() => browserHistory.push("/create")}
                  style={{
                    fontWeight: "400",
                    margin: "0em 1em",
                    lineHeight: "25px",
                    height: "25px"
                  }}
                >
                  + Add New
                </StyledButton>
              </UploadButtonWrapper>
              <UploadButtonWrapper style={{ marginRight: 0, marginLeft: 0 }}>
                <StyledButton
                  onClick={() => browserHistory.push("/export")}
                  style={{
                    fontWeight: "400",
                    margin: "0em 1em 0 0",
                    lineHeight: "25px",
                    height: "25px"
                  }}
                >
                  Export
                </StyledButton>
              </UploadButtonWrapper>
            </div>
          ) : null}
        </div>
      );
    }

    if (this.state.newTransfer) {
      var newTransfer = (
        <NewTransferManager
          transfer_account_ids={this.get_selected_ids_array(
            this.state.idSelectedStatus
          )}
          cancelNewTransfer={() => this.onNewTransfer()}
        />
      );
    } else {
      newTransfer = null;
    }

    if (this.props.transferAccounts.loadStatus.isRequesting) {
      return (
        <div
          style={{ display: "flex", justifyContent: "center", margin: "1em" }}
        >
          <LoadingSpinner />
        </div>
      );
    }

    if (
      this.props.transferAccounts.loadStatus.success &&
      filteredData !== null &&
      filteredData !== undefined
    ) {
      return (
        <div style={{ display: "flex", flexDirection: "column" }}>
          {newTransfer}

          <ModuleBox style={{ width: "calc(100% - 2em)" }}>
            <Wrapper>
              <TopRow>{topBarContent}</TopRow>
              <ReactTable
                columns={[
                  {
                    Header: "",
                    id: "transferAccountIcon",
                    accessor: transferAccount =>
                      this._customIcon(transferAccount),
                    headerClassName: "react-table-header",
                    width: 40,
                    sortable: false
                  },
                  {
                    Header: "Name",
                    id: "transferAccountName",
                    accessor: transferAccount =>
                      this._customName(transferAccount),
                    headerClassName: "react-table-header",
                    className: "react-table-first-cell"
                  },
                  {
                    Header: "Created",
                    accessor: "created",
                    headerClassName: "react-table-header",
                    Cell: cellInfo => <DateTime created={cellInfo.value} />
                  },
                  {
                    Header: "Balance",
                    accessor: "balance",
                    headerClassName: "react-table-header",
                    Cell: cellInfo => {
                      const token =
                        cellInfo.original.token &&
                        cellInfo.original.token.symbol;
                      const money = formatMoney(
                        cellInfo.value / 100,
                        undefined,
                        undefined,
                        undefined,
                        token
                      );
                      return <p style={{ margin: 0 }}>{money}</p>;
                    }
                  },
                  {
                    Header: "Status",
                    accessor: "is_approved",
                    headerClassName: "react-table-header",
                    Cell: cellInfo => (
                      <p style={{ margin: 0, cursor: "pointer" }}>
                        {cellInfo.value === true ? "Approved" : "Unapproved"}
                      </p>
                    )
                  },
                  {
                    Header: () => (
                      <input
                        type="checkbox"
                        checked={this.state.allCheckedTransferAccounts}
                        onChange={() =>
                          this.checkAllTransferAccounts(filteredData)
                        }
                      />
                    ),
                    accessor: "id",
                    headerClassName: "react-table-header",
                    width: 60,
                    sortable: false,
                    Cell: cellInfo => this.displaySelect(cellInfo.value)
                  }
                ]}
                loading={loadingStatus} // Display the loading overlay when we need it
                data={filteredData}
                pageSize={20}
                sortable={true}
                showPagination={true}
                showPageSizeOptions={false}
                className="react-table"
                resizable={false}
                getTrProps={(state, rowInfo, instance) => {
                  if (rowInfo) {
                    return {
                      style: {
                        cursor: rowInfo.row ? "pointer" : null
                      }
                    };
                  }
                  return {};
                }}
                getTdProps={(state, rowInfo, column) => {
                  return {
                    onClick: (e, handleOriginal) => {
                      // handle click on checkbox
                      if (column.id === "id") {
                        this.toggleSelectedTransferAccount(rowInfo.original.id);
                        return;
                      }

                      if (rowInfo && rowInfo.row) {
                        browserHistory.push("/accounts/" + rowInfo.row.id);
                      }

                      if (handleOriginal) {
                        handleOriginal();
                      }
                    }
                  };
                }}
              />
            </Wrapper>
          </ModuleBox>
        </div>
      );
    }

    return (
      <ModuleBox>
        <p style={{ padding: "1em", textAlign: "center" }}>
          No transfer accounts found
        </p>
      </ModuleBox>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TransferAccountList);

const UserSVG = styled.img`
  cursor: pointer;
  width: 20px;
  height: 20px;
`;

const UploadButtonWrapper = styled.div`
  margin: auto 1em;
`;
