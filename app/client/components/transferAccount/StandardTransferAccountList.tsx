import * as React from "react";
import { connect } from "react-redux";
import { Modal, Button, InputNumber, Space } from "antd";

import { ReduxState, sempoObjects } from "../../reducers/rootReducer";
import { EditTransferAccountPayload } from "../../reducers/transferAccount/types";
import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import TransferAccountList from "./TransferAccountList";
import ImportModal from "./importModal.jsx";

import { browserHistory } from "../../createStore";
import { CreateBulkTransferBody } from "../../reducers/bulkTransfer/types";
import { CreateRequestAction } from "../../genericState/types";
import { getActiveToken } from "../../utils";
import { apiActions } from "../../genericState";

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
}

interface OuterProps {}

interface ComponentState {
  importModalVisible: boolean;
  bulkTransferModalVisible: boolean;
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
    // TODO: need to construct the generic properly for this
    // @ts-ignore
    bulkTransfers: state.bulkTransfers
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    editTransferAccountRequest: (payload: EditTransferAccountPayload) =>
      dispatch(EditTransferAccountAction.editTransferAccountRequest(payload)),
    createBulkTransferRequest: (body: CreateBulkTransferBody) =>
      dispatch(apiActions.create(sempoObjects.bulkTransfers, body))
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

  toggleImportModal() {
    this.setState({ importModalVisible: !this.state.importModalVisible });
  }

  showBulkTransferModal() {
    this.setState({ bulkTransferModalVisible: true });
  }

  handleBulkCancel() {
    this.setState({ bulkTransferModalVisible: false, amount: 0 });
  }

  setApproval(approve: boolean, transfer_account_id_list: React.Key[]) {
    this.props.editTransferAccountRequest({
      body: {
        transfer_account_id_list,
        approve
      }
    });
  }

  updateQueryData(query: Query) {
    this.setState({
      params: query.params,
      searchString: query.searchString
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
        onClick: (IdList: React.Key[]) => this.setApproval(true, IdList)
      },
      {
        label: "Unapprove",
        onClick: (IdList: React.Key[]) => this.setApproval(false, IdList)
      },
      {
        label: "New Bulk Disbursement",
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
        />
        <TransferAccountList
          orderedTransferAccounts={transferAccounts.IdList}
          actionButtons={actionButtons}
          noneSelectedbuttons={noneSelectedButtons}
          onSelectChange={(s: React.Key[], u: React.Key[], a: boolean) =>
            this.onSelectChange(s, u, a)
          }
        />
        <ImportModal
          isModalVisible={importModalVisible}
          handleOk={() => this.toggleImportModal()}
          handleCancel={() => this.toggleImportModal()}
        />

        <Modal
          title="Create New Bulk Disbursement"
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
          <Space>
            <span>Disbursement Amount: </span>
            <InputNumber
              min={0}
              onChange={(amount: numberInput) => this.setState({ amount })}
            />
            {this.props.activeToken.symbol}
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
