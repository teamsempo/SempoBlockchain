import * as React from "react";
import { connect } from "react-redux";
import { message } from "antd";

import HistoryDrawer from "../history/historyDrawer";
import {
  LoadTransferUsagePayload,
  TransferUsage
} from "../../reducers/transferUsage/types";
import { ReduxState } from "../../reducers/rootReducer";
import EditUserForm, { IEditUser } from "./EditUserForm";
import {
  DeleteUserAction,
  EditUserAction,
  ResetPinAction,
  LoadUserHistoryAction
} from "../../reducers/user/actions";
import {
  User,
  ResetPinPayload,
  DeleteUserPayload
} from "../../reducers/user/types";

import { EditTransferCardAction } from "../../reducers/transferCard/actions";
import { LoadTransferUsagesAction } from "../../reducers/transferUsage/actions";

interface DispatchProps {
  getHistory: (path: number) => LoadUserHistoryAction;
  loadUsages: (payload: LoadTransferUsagePayload) => LoadTransferUsagesAction;
  editUser: (body: User, path: number) => EditUserAction;
  resetPin: (payload: ResetPinPayload) => ResetPinAction;
  deleteUser: (payload: DeleteUserPayload) => DeleteUserAction;
  editTransferCard: (
    body: any,
    path: string,
    userId: number
  ) => EditTransferCardAction;
}

interface StateProps {
  transferCard: ReduxState["transferCard"];
  users: ReduxState["users"];
  selectedUser: any;
  history: [];
  transferUsages: TransferUsage[];
}

interface OuterProps {
  userId: number;
}

type Props = DispatchProps & StateProps & OuterProps;

interface attr_dict {
  [key: string]: string;
}

class SingleUserManagement extends React.Component<Props> {
  constructor(props: any) {
    super(props);
    this.state = {
      viewHistory: false
    };
  }
  onEditUser(form: IEditUser) {
    const { selectedUser } = this.props;

    let businessUsage = form.businessUsage;
    if (businessUsage && businessUsage.toLowerCase() === "other") {
      businessUsage = form.usageOtherSpecific;
    }

    let custom_attr_keys =
      selectedUser && Object.keys(selectedUser.custom_attributes);
    let attr_dict = {};
    custom_attr_keys.map(key => {
      (attr_dict as attr_dict)[key] = form[key];
      return attr_dict;
    });
    this.props.editUser(
      {
        first_name: form.firstName,
        last_name: form.lastName,
        public_serial_number: form.publicSerialNumber,
        phone: form.phone ? "+" + form.phone : undefined,
        location: form.location,
        account_types: form.accountTypes,
        referred_by: form.referredBy,
        custom_attributes: attr_dict,
        business_usage_name: businessUsage
      },
      this.props.userId
    );
  }

  componentDidUpdate(prevProps: any) {
    if (
      prevProps.users.editStatus.isRequesting !==
      this.props.users.editStatus.isRequesting
    ) {
      if (prevProps.users.editStatus.isRequesting) {
        this.props.loadUsages({ query: { show_all: true } });
      }
    }
  }

  onResetPin() {
    const { selectedUser } = this.props;
    window.confirm(
      `Are you sure you wish to reset ${selectedUser.first_name} ${selectedUser.last_name}'s PIN?`
    ) && this.props.resetPin({ body: { user_id: this.props.selectedUser.id } });
  }

  onDeleteUser() {
    const { selectedUser } = this.props;
    let del = window.prompt(
      `Are you sure you wish to delete participant "${selectedUser.first_name} ${selectedUser.last_name}"? This will also delete any associated transfer cards permanently. This action cannot be undone. Type DELETE to confirm`
    );
    if (del === "DELETE") {
      this.props.deleteUser({ path: selectedUser.id });
    } else {
      message.error("Action Canceled");
    }
  }

  onDisableCard() {
    if (
      this.props.selectedUser.transfer_card &&
      this.props.selectedUser.transfer_card.is_disabled
    ) {
      window.alert("This card has already been disabled.");
      return;
    }

    if (
      !window.confirm(
        "Warning: A card that has been disabled cannot be re-enabled. Continue?"
      )
    ) {
      return;
    }

    this.props.editTransferCard(
      { disable: true },
      this.props.selectedUser.public_serial_number,
      this.props.selectedUser.id
    );
  }

  onViewHistory() {
    this.setState(prevState => ({
      viewHistory: !prevState.viewHistory
    }));
    this.props.getHistory(this.props.selectedUser.id);
  }
  render() {
    return (
      <div>
        <HistoryDrawer
          drawerVisible={this.state.viewHistory}
          onClose={() => this.onViewHistory()}
          changes={this.props.history}
        />
        <EditUserForm
          transferCard={this.props.transferCard}
          users={this.props.users}
          selectedUser={this.props.selectedUser}
          transferUsages={this.props.transferUsages}
          onSubmit={(form: IEditUser) => this.onEditUser(form)}
          onResetPin={() => this.onResetPin()}
          onDeleteUser={() => this.onDeleteUser()}
          onDisableCard={() => this.onDisableCard()}
          onViewHistory={() => this.onViewHistory()}
        />
      </div>
    );
  }
}

const mapStateToProps = (state: ReduxState, ownProps: any): StateProps => {
  return {
    transferCard: state.transferCard,
    users: state.users,
    selectedUser: state.users.byId[parseInt(ownProps.userId)],
    history: state.users.loadHistory.changes,
    transferUsages: state.transferUsages.transferUsages
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    getHistory: (path: number) =>
      dispatch(LoadUserHistoryAction.loadUserHistoryRequest({ path })),
    loadUsages: payload =>
      dispatch(LoadTransferUsagesAction.loadTransferUsagesRequest(payload)),
    editUser: (body: User, path: number) =>
      dispatch(EditUserAction.editUserRequest({ body, path })),
    resetPin: payload => dispatch(ResetPinAction.resetPinRequest(payload)),
    deleteUser: payload =>
      dispatch(DeleteUserAction.deleteUserRequest(payload)),
    editTransferCard: (body: any, path: string, userId) =>
      dispatch(
        EditTransferCardAction.editTransferCardRequest({ body, path, userId })
      )
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(SingleUserManagement);
