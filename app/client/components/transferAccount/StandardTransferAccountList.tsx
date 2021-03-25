import * as React from "react";
import { connect } from "react-redux";
import { Modal, Button, InputNumber, Space, Select } from "antd";
const { Option } = Select;

import { ReduxState, sempoObjects } from "../../reducers/rootReducer";
import {
  EditTransferAccountPayload,
  LoadTransferAccountListPayload
} from "../../reducers/transferAccount/types";
import {
  EditTransferAccountAction,
  LoadTransferAccountAction
} from "../../reducers/transferAccount/actions";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import TransferAccountList from "./TransferAccountList";
import ImportModal from "./import/importModal.jsx";

import { browserHistory } from "../../createStore";
import {
  CreateBulkTransferBody,
  TransferTypes
} from "../../reducers/bulkTransfer/types";
import { getActiveToken } from "../../utils";
import { apiActions, CreateRequestAction } from "../../genericState";

type numberInput = string | number | null | undefined;

interface StateProps {
  activeToken: any;
  transferAccounts: any;
  bulkTransfers: any;
}

interface DispatchProps {
  editTransferAccountRequest: (
    payload: EditTransferAccountPayload
  ) => EditTransferAccountAction;
  createBulkTransferRequest: (
    body: CreateBulkTransferBody
  ) => CreateRequestAction;
  loadTransferAccountList: ({
    query,
    path
  }: LoadTransferAccountListPayload) => LoadTransferAccountAction;
}

interface OuterProps {}

interface ComponentState {
  importModalVisible: boolean;
  bulkTransferModalVisible: boolean;
  amount: numberInput;
  transferType: TransferTypes;
  selectedRowKeys: React.Key[];
  unselectedRowKeys: React.Key[];
  allSelected: boolean;
  params: string;
  searchString: string;
  awaitingEditSuccess: boolean;
  page: number;
  per_page: number;
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
    editTransferAccountRequest: (payload: EditTransferAccountPayload) =>
      dispatch(EditTransferAccountAction.editTransferAccountRequest(payload)),
    createBulkTransferRequest: (body: CreateBulkTransferBody) =>
      dispatch(apiActions.create(sempoObjects.bulkTransfers, body)),
    loadTransferAccountList: ({
      query,
      path
    }: LoadTransferAccountListPayload) =>
      dispatch(
        LoadTransferAccountAction.loadTransferAccountsRequest({ query, path })
      )
  };
};

class StandardTransferAccountList extends React.Component<
  Props,
  ComponentState
> {
  constructor(props: Props) {
    super(props);
    this.state = {
      importModalVisible: false,
      bulkTransferModalVisible: false,
      amount: 0,
      transferType: "DISBURSEMENT",
      selectedRowKeys: [],
      unselectedRowKeys: [],
      allSelected: false,
      params: "",
      searchString: "",
      awaitingEditSuccess: false,
      page: 1,
      per_page: 10
    };
  }

  componentDidUpdate(prevProps: Props) {
    if (
      this.props.transferAccounts.editStatus.isRequesting == true &&
      prevProps.transferAccounts.editStatus.isRequesting == false
    ) {
      //Set a flag so that if the transferAccounts edit status swaps to success, we'll reload the list
      this.setState({ awaitingEditSuccess: true });
    } else if (
      this.state.awaitingEditSuccess &&
      this.props.transferAccounts.editStatus.success == true
    ) {
      // Update transfer list by re-running server-side search
      this.setState({ awaitingEditSuccess: false });
      this.props.loadTransferAccountList({
        query: {
          params: this.state.params,
          search_string: this.state.searchString,
          page: this.state.page,
          per_page: this.state.per_page
        }
      });
    }
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

  onPaginateChange = (page: number, pageSize: number | undefined) => {
    let per_page = pageSize || 10;
    this.setState({
      page,
      per_page
    });
  };

  toggleImportModal() {
    this.setState({ importModalVisible: !this.state.importModalVisible });
  }

  showBulkTransferModal() {
    this.setState({ bulkTransferModalVisible: true });
  }

  handleBulkCancel() {
    this.setState({ bulkTransferModalVisible: false, amount: 0 });
  }

  setApproval(approve: boolean) {
    let { selectedRowKeys, unselectedRowKeys, allSelected } = this.state;

    let include_accounts, exclude_accounts;

    if (allSelected) {
      //If the "select all" box is true, only specify the accounts to exclude,
      // as leaving "include_accounts" blank defaults to everything
      exclude_accounts = unselectedRowKeys;
    } else {
      //If the "select all" box is false, only specify the accounts to include.
      include_accounts = selectedRowKeys;
    }

    this.props.editTransferAccountRequest({
      body: {
        approve,
        params: this.state.params,
        search_string: this.state.searchString,
        include_accounts: include_accounts,
        exclude_accounts: exclude_accounts
      },
      path: "bulk"
    });
  }

  updateQueryData(query: Query) {
    this.setState({
      params: query.params,
      searchString: query.searchString,
      page: 1
    });
  }

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

    //We can typecast because the button is only available if the number is set
    let amount = 100 * (this.state.amount as number);

    this.props.createBulkTransferRequest({
      disbursement_amount: amount,
      transfer_type: this.state.transferType,
      params: this.state.params,
      search_string: this.state.searchString,
      include_accounts: include_accounts,
      exclude_accounts: exclude_accounts
    });
  }

  render() {
    const { transferAccounts, bulkTransfers } = this.props;
    const { importModalVisible, amount } = this.state;

    let numberSet = typeof amount === "number" && amount !== 0;

    const actionButtons = [
      {
        label: "Approve",
        onClick: (IdList: React.Key[]) => this.setApproval(true)
      },
      {
        label: "Unapprove",
        onClick: (IdList: React.Key[]) => this.setApproval(false)
      },
      {
        label: "New Bulk Transfer",
        onClick: (IdList: React.Key[]) => this.showBulkTransferModal()
      }
    ];

    const noneSelectedButtons = [
      {
        label: "Import",
        onClick: () => this.toggleImportModal()
      },
      {
        label: "Export",
        onClick: () => browserHistory.push("/export")
      }
    ];

    return (
      <>
        <QueryConstructor
          onQueryChange={(query: Query) => this.updateQueryData(query)}
          filterObject="user"
          pagination={{
            page: this.state.page,
            per_page: this.state.per_page
          }}
        />
        <TransferAccountList
          orderedTransferAccounts={transferAccounts.IdList}
          actionButtons={actionButtons}
          noneSelectedbuttons={noneSelectedButtons}
          onSelectChange={(s: React.Key[], u: React.Key[], a: boolean) =>
            this.onSelectChange(s, u, a)
          }
          paginationOptions={{
            currentPage: this.state.page,
            items: this.props.transferAccounts.pagination.items,
            onChange: (page: number, perPage: number | undefined) =>
              this.onPaginateChange(page, perPage)
          }}
        />
        <ImportModal
          isModalVisible={importModalVisible}
          handleOk={() => this.toggleImportModal()}
          handleCancel={() => this.toggleImportModal()}
        />

        <Modal
          title="Create New Bulk Transfer"
          visible={this.state.bulkTransferModalVisible}
          onOk={this.createBulkTransferFromState}
          confirmLoading={bulkTransfers.createStatus.isRequesting}
          onCancel={() => this.handleBulkCancel()}
          footer={[
            <Button key="back" onClick={() => this.handleBulkCancel()}>
              Cancel
            </Button>,
            <Button
              key="submit"
              type="primary"
              disabled={this.state.selectedRowKeys.length === 0 || !numberSet}
              loading={bulkTransfers.createStatus.isRequesting}
              onClick={() => this.createBulkTransferFromState()}
            >
              Create
            </Button>
          ]}
        >
          <Space direction="vertical" size="large">
            <Space>
              <span>Transfer Type: </span>
              <Select
                defaultValue="DISBURSEMENT"
                style={{ width: 240 }}
                onChange={(transferType: TransferTypes) =>
                  this.setState({ transferType })
                }
              >
                <Option value="DISBURSEMENT">Disbursement</Option>
                <Option value="RECLAMATION">Reclamation</Option>
                <Option value="BALANCE">Balance</Option>
              </Select>
            </Space>
            <Space>
              <span>Transfer Amount: </span>
              <InputNumber
                min={0}
                onChange={(amount: numberInput) => this.setState({ amount })}
              />
              {this.props.activeToken.symbol}
            </Space>
          </Space>
        </Modal>
      </>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(StandardTransferAccountList);
