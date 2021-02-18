import * as React from "react";
import { connect } from "react-redux";
import { Card, Button, InputNumber, Space } from "antd";

import { ReduxState, sempoObjects } from "../../reducers/rootReducer";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import { ActionButton, NoneSelectedButton } from "./transferAccountList";
import TransferAccountList from "./TransferAccountList";

import { CreateBulkTransferBody } from "../../reducers/bulkTransfer/types";

import { CreateRequestAction } from "../../genericState/types";
import { apiActions } from "../../genericState";
import { getActiveToken } from "../../utils";

type numberInput = string | number | null | undefined;

interface StateProps {
  activeToken: any;
  transferAccounts: any;
  bulkTransfers: any;
}

interface DispatchProps {
  createBulkTransferRequest: (
    body: CreateBulkTransferBody
  ) => CreateRequestAction;
}

interface OuterProps {}

interface ComponentState {
  amount: numberInput;
  selectedRowKeys: React.Key[];
  unselectedRowKeys: React.Key[];
  allSelected: boolean;
  params: string;
  searchString: string;
}

type Props = StateProps & DispatchProps & OuterProps;

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    activeToken: getActiveToken(state),
    transferAccounts: state.transferAccounts,
    bulkTransfers: state.bulkTransfers
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    createBulkTransferRequest: (body: CreateBulkTransferBody) =>
      dispatch(apiActions.create(sempoObjects.bulkTransfers, body))
  };
};

class BulkDisbursementTransferAccountList extends React.Component<
  Props,
  ComponentState
> {
  constructor(props: Props) {
    super(props);
    this.state = {
      amount: 0,
      selectedRowKeys: [],
      unselectedRowKeys: [],
      allSelected: false,
      params: "",
      searchString: ""
    };
  }

  onSelectChange = (
    selectedRowKeys: React.Key[],
    unselectedRowKeys: React.Key[],
    allSelected: boolean
  ) => {
    this.setState({
      selectedRowKeys,
      unselectedRowKeys,
      allSelected
    });
  };

  createBulkTransferFromState() {
    let { selectedRowKeys, unselectedRowKeys, allSelected } = this.state;
    this.createBulkTransfer(selectedRowKeys, unselectedRowKeys, allSelected);
  }

  createBulkTransfer(
    selected: React.Key[],
    unSelected: React.Key[],
    allSelected: boolean
  ) {
    let include_accounts, exclude_accounts;

    if (allSelected) {
      //If the "select all" box is true, only specify the accounts to exclude,
      // as leaving "include_accounts" blank defaults to everything
      exclude_accounts = unSelected;
    } else {
      //If the "select all" box is false, only specify the accounts to include.
      include_accounts = selected;
    }

    this.props.createBulkTransferRequest({
      disbursement_amount: 100,
      params: this.state.params,
      search_string: this.state.searchString,
      include_accounts: include_accounts,
      exclude_accounts: exclude_accounts
    });
  }

  updateQueryData(query: Query) {
    this.setState({
      params: query.params,
      searchString: query.searchString
    });
  }

  render() {
    const { transferAccounts, bulkTransfers } = this.props;
    const { amount } = this.state;

    let numberSet = typeof amount === "number" && amount !== 0;

    const actionButtons: ActionButton[] = [];
    const noneSelectedButtons: NoneSelectedButton[] = [];

    return (
      <Card title="Create Bulk Disbursement" style={{ margin: "10px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end"
          }}
        >
          <h3>Disbursement Amount:</h3>

          <Button
            onClick={() => this.createBulkTransferFromState()}
            disabled={this.state.selectedRowKeys.length === 0 || !numberSet}
            loading={bulkTransfers.createStatus.isRequesting}
            style={{ margin: "10px" }}
          >
            Create
          </Button>
        </div>

        <Space style={{ margin: "10px", marginBottom: "30px" }}>
          <InputNumber
            min={0}
            onChange={(amount: numberInput) => this.setState({ amount })}
          />
          {this.props.activeToken.symbol}
        </Space>

        <h3>Recipients:</h3>

        <QueryConstructor
          filterObject="user"
          onQueryChange={(query: Query) => this.updateQueryData(query)}
        />
        <TransferAccountList
          orderedTransferAccounts={transferAccounts.IdList}
          actionButtons={actionButtons}
          noneSelectedbuttons={noneSelectedButtons}
          onSelectChange={(s: React.Key[], u: React.Key[], a: boolean) =>
            this.onSelectChange(s, u, a)
          }
        />
      </Card>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BulkDisbursementTransferAccountList);
