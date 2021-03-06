import * as React from "react";
import { connect } from "react-redux";
import { Modal, Button, InputNumber, Space } from "antd";

import { ReduxState } from "../../reducers/rootReducer";
import { EditTransferAccountPayload } from "../../reducers/transferAccount/types";
import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import TransferAccountList from "./TransferAccountList";
import ImportModal from "./import/importModal.jsx";

import { browserHistory } from "../../createStore";
import { getActiveToken } from "../../utils";

type numberInput = string | number | null | undefined;

interface StateProps {
  activeToken: any;
  transferAccounts: any;
}

interface DispatchProps {
  editTransferAccountRequest: (
    payload: EditTransferAccountPayload
  ) => EditTransferAccountAction;
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
    transferAccounts: state.transferAccounts
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    editTransferAccountRequest: (payload: EditTransferAccountPayload) =>
      dispatch(EditTransferAccountAction.editTransferAccountRequest(payload))
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

  render() {
    const { transferAccounts } = this.props;
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
      </>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(StandardTransferAccountList);
