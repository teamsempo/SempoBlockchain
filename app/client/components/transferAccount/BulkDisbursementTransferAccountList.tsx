import * as React from "react";
import { connect } from "react-redux";

import { ReduxState, sempoObjects } from "../../reducers/rootReducer";
import { EditTransferAccountPayload } from "../../reducers/transferAccount/types";
import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import TransferAccountList, {
  ActionButton,
  NoneSelectedButton,
  TransferAccount
} from "../transferAccount/transferAccountList";
import {
  CreateBulkTransferBody,
  CreateBulkTransferPayload
} from "../../reducers/bulkTransfer/types";
import { CreateBulkTransferAction } from "../../reducers/bulkTransfer/actions";
import {
  ApiRequestAction,
  CreateRequestAction
} from "../../genericState/types";
import { apiActions } from "../../genericState";

interface StateProps {
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
  transfer_account_id_list: React.Key[];
  params: string;
  searchString: string;
}

type Props = StateProps & DispatchProps & OuterProps;

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    transferAccounts: state.transferAccounts,
    bulkTransfers: state.bulkTransfers
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    createBulkTransferRequest: (body: CreateBulkTransferBody) =>
      dispatch(apiActions.create(sempoObjects.BULK, body))
  };
};

class BulkDisbursementTransferAccountList extends React.Component<
  Props,
  ComponentState
> {
  constructor(props: Props) {
    super(props);
    this.state = {
      transfer_account_id_list: [],
      params: "",
      searchString: ""
    };
  }

  onSelectChange(
    selectedRowKeys: React.Key[],
    selectedRows: TransferAccount[]
  ) {
    this.setState({ transfer_account_id_list: selectedRowKeys });
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

    const actionButtons: ActionButton[] = [
      {
        label: "Create Bulk Transfer",
        onClick: (
          selected: React.Key[],
          unSelected: React.Key[],
          allSelected: boolean
        ) => this.createBulkTransfer(selected, unSelected, allSelected),
        loading: bulkTransfers.createStatus.isRequesting
      }
    ];

    const noneSelectedButtons: NoneSelectedButton[] = [];

    return (
      <div style={{ margin: "10px" }}>
        <QueryConstructor
          filterObject="user"
          onQueryChange={(query: Query) => this.updateQueryData(query)}
        />
        <TransferAccountList
          orderedTransferAccounts={transferAccounts.IdList}
          actionButtons={actionButtons}
          noneSelectedbuttons={noneSelectedButtons}
        />
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BulkDisbursementTransferAccountList);
