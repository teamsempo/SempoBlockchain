import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";
import { EditTransferAccountPayload } from "../../reducers/transferAccount/types";
import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";

import QueryConstructor from "../filterModule/queryConstructor";
import TransferAccountList, {
  ActionButton,
  NoneSelectedButton,
  TransferAccount
} from "../transferAccount/transferAccountList";
import { CreateBulkTransferPayload } from "../../reducers/bulkTransfer/types";
import { CreateBulkTransferAction } from "../../reducers/bulkTransfer/actions";

interface StateProps {
  transferAccounts: any;
  bulkTransfers: any;
}

interface DispatchProps {
  createBulkTransferRequest: (
    payload: CreateBulkTransferPayload
  ) => CreateBulkTransferAction;
}

interface OuterProps {}

interface ComponentState {
  transfer_account_id_list: React.Key[];
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
    createBulkTransferRequest: (payload: CreateBulkTransferPayload) =>
      dispatch(CreateBulkTransferAction.createBulkTransferRequest(payload))
  };
};

class BulkDisbursementTransferAccountList extends React.Component<
  Props,
  ComponentState
> {
  constructor(props: Props) {
    super(props);
    this.state = {
      transfer_account_id_list: []
    };
  }

  onSelectChange(
    selectedRowKeys: React.Key[],
    selectedRows: TransferAccount[]
  ) {
    this.setState({ transfer_account_id_list: selectedRowKeys });
  }

  createBulkTransfer(transfer_account_id_list: React.Key[]) {
    this.props.createBulkTransferRequest({
      body: {
        disbursement_amount: 100
      }
    });
  }

  render() {
    const { transferAccounts, bulkTransfers } = this.props;

    const actionButtons: ActionButton[] = [
      {
        label: "Create Bulk Transfer",
        onClick: (IdList: React.Key[]) => this.createBulkTransfer(IdList),
        loading: bulkTransfers.createStatus.isRequesting
      }
    ];

    const noneSelectedButtons: NoneSelectedButton[] = [];

    return (
      <div style={{ margin: "10px" }}>
        <QueryConstructor filterObject="user" />
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
