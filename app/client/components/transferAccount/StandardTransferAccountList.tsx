import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";

import QueryConstructor from "../filterModule/queryConstructor";
import TransferAccountList from "../transferAccount/newTransferAccountList";
import { EditTransferAccountPayload } from "../../reducers/transferAccount/types";
import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";
import { CreateUserPayload } from "../../reducers/user/types";

interface StateProps {
  transferAccounts: any;
}

interface DispatchProps {
  editTransferAccountRequest: (
    payload: EditTransferAccountPayload
  ) => EditTransferAccountAction;
}

interface OuterProps {}

interface ComponentState {}

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
  setApproval(approve: boolean, transfer_account_id_list: React.Key[]) {
    this.props.editTransferAccountRequest({
      body: {
        transfer_account_id_list,
        approve
      }
    });
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
      }
    ];

    if (transferAccounts.IdList) {
      return (
        <div>
          <QueryConstructor filterObject="user" />
          <TransferAccountList
            orderedTransferAccounts={transferAccounts.IdList}
            actionButtons={actionButtons}
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
