import * as React from "react";
import { connect } from "react-redux";
import { Modal, Button, InputNumber, Space, Select, Input } from "antd";
const { Option } = Select;

import { ReduxState, sempoObjects } from "../../reducers/rootReducer";
import {
  EditTransferAccountPayload,
  LoadTransferAccountListPayload,
} from "../../reducers/transferAccount/types";
import {
  EditTransferAccountAction,
  LoadTransferAccountAction,
} from "../../reducers/transferAccount/actions";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import TransferAccountList from "./TransferAccountList";
import ImportModal from "./import/importModal.jsx";
import ExportModal from "./export/exportModal.jsx";

import {
  CreateBulkTransferBody,
  TransferTypes,
} from "../../reducers/bulkTransfer/types";
import { getActiveToken } from "../../utils";
import { apiActions, CreateRequestAction } from "../../genericState";

type numberInput = string | number | null | undefined;

interface StateProps {
  adminTier: any;
  activeToken: any;
  transferAccounts: any;
  bulkTransfers: any;
  login: any;
  organisations: any;
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
    path,
  }: LoadTransferAccountListPayload) => LoadTransferAccountAction;
}

interface OuterProps {}

interface ComponentState {
  exportModalVisible: boolean;
  importModalVisible: boolean;
  bulkTransferModalVisible: boolean;
  amount: numberInput;
  transferType: TransferTypes;
  label: string;
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
    adminTier: state.login.adminTier,
    activeToken: getActiveToken(state),
    transferAccounts: state.transferAccounts,
    bulkTransfers: state.bulkTransfers,
    login: state.login,
    organisations: state.organisations,
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
      path,
    }: LoadTransferAccountListPayload) =>
      dispatch(
        LoadTransferAccountAction.loadTransferAccountsRequest({ query, path })
      ),
  };
};

class StandardTransferAccountList extends React.Component<
  Props,
  ComponentState
> {
  constructor(props: Props) {
    super(props);
    const defaultDisbusement =
      props.organisations.byId[props.login.organisationId]
        .default_disbursement / 100 || 0;
    this.state = {
      exportModalVisible: false,
      importModalVisible: false,
      bulkTransferModalVisible: false,
      amount: defaultDisbusement,
      transferType: "DISBURSEMENT",
      selectedRowKeys: [],
      unselectedRowKeys: [],
      allSelected: false,
      params: "",
      label: "",
      searchString: "",
      awaitingEditSuccess: false,
      page: 1,
      per_page: 10,
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
          per_page: this.state.per_page,
        },
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
      allSelected,
    });
  };

  onPaginateChange = (page: number, pageSize: number | undefined) => {
    let per_page = pageSize || 10;
    this.setState({
      page,
      per_page,
    });
  };

  toggleImportModal() {
    this.setState({ importModalVisible: !this.state.importModalVisible });
  }

  toggleExportModal() {
    this.setState({ exportModalVisible: !this.state.exportModalVisible });
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
        exclude_accounts: exclude_accounts,
      },
      path: "bulk",
    });
  }

  updateQueryData(query: Query) {
    this.setState({
      params: query.params,
      searchString: query.searchString,
      page: 1,
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
      label: this.state.label,
      params: this.state.params,
      search_string: this.state.searchString,
      include_accounts: include_accounts,
      exclude_accounts: exclude_accounts,
    });
  }

  render() {
    const { transferAccounts, bulkTransfers, adminTier } = this.props;
    const {
      exportModalVisible,
      importModalVisible,
      amount,
      selectedRowKeys,
      unselectedRowKeys,
      allSelected,
      params,
      searchString,
    } = this.state;

    let include_accounts, exclude_accounts;

    if (allSelected) {
      //If the "select all" box is true, only specify the accounts to exclude,
      // as leaving "include_accounts" blank defaults to everything
      exclude_accounts = unselectedRowKeys;
    } else {
      //If the "select all" box is false, only specify the accounts to include.
      include_accounts = selectedRowKeys;
    }
    const hasSelected =
      allSelected || (include_accounts && include_accounts.length > 0);

    let numberSet =
      typeof amount === "number" &&
      (this.state.transferType === "BALANCE" ? amount >= 0 : amount !== 0);

    const actionButtons = [
      {
        label: "Approve",
        onClick: (IdList: React.Key[]) => this.setApproval(true),
      },
      {
        label: "Unapprove",
        onClick: (IdList: React.Key[]) => this.setApproval(false),
      },
      {
        label: "Create Bulk Transfer",
        onClick: (IdList: React.Key[]) => this.showBulkTransferModal(),
      },
    ];

    const dataButtons = [
      {
        label: "Import",
        onClick: () => this.toggleImportModal(),
      },
      {
        label: "Export",
        onClick: () => this.toggleExportModal(),
      },
    ];

    return (
      <>
        <QueryConstructor
          onQueryChange={(query: Query) => this.updateQueryData(query)}
          filterObject="user"
          disabled={
            !(
              this.props.adminTier === "superadmin" ||
              this.props.adminTier === "sempoadmin"
            )
          }
          pagination={{
            page: this.state.page,
            per_page: this.state.per_page,
          }}
        />
        <TransferAccountList
          params={this.state.params}
          searchString={this.state.searchString}
          orderedTransferAccounts={transferAccounts.IdList}
          actionButtons={actionButtons}
          dataButtons={dataButtons}
          onSelectChange={(s: React.Key[], u: React.Key[], a: boolean) =>
            this.onSelectChange(s, u, a)
          }
          paginationOptions={{
            currentPage: this.state.page,
            items: this.props.transferAccounts.pagination.items,
            onChange: (page: number, perPage: number | undefined) =>
              this.onPaginateChange(page, perPage),
          }}
        />
        <ImportModal
          isModalVisible={importModalVisible}
          handleOk={() => this.toggleImportModal()}
          handleCancel={() => this.toggleImportModal()}
        />

        <ExportModal
          isModalVisible={exportModalVisible}
          handleOk={() => this.toggleExportModal()}
          handleCancel={() => this.toggleExportModal()}
          params={params}
          search_string={searchString}
          include_accounts={include_accounts}
          exclude_accounts={exclude_accounts}
          hasSelected={hasSelected}
        />

        <Modal
          title="Create Bulk Transfer"
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
            </Button>,
          ]}
        >
          <Space direction="vertical" size="large">
            <Space>
              <span>Label: </span>
              <Input
                placeholder="Untitled"
                onChange={(e) => this.setState({ label: e.target.value })}
              />
            </Space>
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
                defaultValue={Number(amount)}
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
