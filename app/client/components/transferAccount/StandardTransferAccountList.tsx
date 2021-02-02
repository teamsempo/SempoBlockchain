import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";
import { EditTransferAccountPayload } from "../../reducers/transferAccount/types";
import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";

import QueryConstructor from "../filterModule/queryConstructor";
import TransferAccountList, {
  TransferAccount
} from "../transferAccount/newTransferAccountList";
import NewTransferManager from "../management/newTransferManager.jsx";

interface StateProps {
  transferAccounts: any;
}

interface DispatchProps {
  editTransferAccountRequest: (
    payload: EditTransferAccountPayload
  ) => EditTransferAccountAction;
}

interface OuterProps {}

interface ComponentState {
  newTransfer: boolean;
  transfer_account_id_list: React.Key[];
}

type Props = StateProps & DispatchProps & OuterProps;

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
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
      newTransfer: false,
      transfer_account_id_list: []
    };
  }

  onSelectChange = (
    selectedRowKeys: React.Key[],
    selectedRows: TransferAccount[]
  ) => {
    this.setState({ transfer_account_id_list: selectedRowKeys });
  };

  setApproval(approve: boolean, transfer_account_id_list: React.Key[]) {
    this.props.editTransferAccountRequest({
      body: {
        transfer_account_id_list,
        approve
      }
    });
  }

  activateNewTransfer(transfer_account_id_list: React.Key[]) {
    this.setState({
      newTransfer: true
    });
  }

  cancelNewTransfer() {
    this.setState({ newTransfer: false });
  }

  render() {
    const { transferAccounts } = this.props;

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
        label: "New Transfer",
        onClick: (IdList: React.Key[]) => this.activateNewTransfer(IdList)
      }
    ];

    if (this.state.newTransfer) {
      var newTransfer = (
        <NewTransferManager
          transfer_account_ids={this.state.transfer_account_id_list}
          cancelNewTransfer={() => this.cancelNewTransfer()}
        />
      );
    } else {
      newTransfer = <></>;
    }

    if (transferAccounts.IdList) {
      return (
        <div>
          {newTransfer}
          <QueryConstructor filterObject="user" />
          <TransferAccountList
            orderedTransferAccounts={transferAccounts.IdList}
            actionButtons={actionButtons}
            noneSelectedbuttons={[]}
          />
        </div>
      );
    }

    return <div>loading</div>;
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(StandardTransferAccountList);
