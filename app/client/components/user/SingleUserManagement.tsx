import * as React from "react";
import { connect } from "react-redux";

import { editUser, resetPin, deleteUser } from "../../reducers/userReducer";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { ReduxState } from "../../reducers/rootReducer";
import EditUserForm, { IEditUser } from "./EditUserForm";
import { TransferAccountTypes } from "../transferAccount/types";
import { MessageAction } from "../../reducers/message/actions";

interface DispatchProps {
  //todo(typescript): editUser body should be written in EditUserPayload from reducers/user/types.ts
  editUser: (body: any, path: string) => void;
  resetPin: (body: { user_id: number }) => void;
  deleteUser: (path: string) => void;
  addMsg: (msg: string) => void;
}

interface StateProps {
  users: any;
  selectedUser: any;
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
  onEditUser(form: IEditUser) {
    const user_id = this.props.userId.toString();
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
        phone: form.phone,
        location: form.location,
        is_vendor:
          form.accountType === TransferAccountTypes.VENDOR ||
          form.accountType === TransferAccountTypes.CASHIER,
        is_tokenagent: form.accountType === TransferAccountTypes.TOKENAGENT,
        is_groupaccount: form.accountType === TransferAccountTypes.GROUPACCOUNT,
        referred_by: form.referredBy,
        custom_attributes: attr_dict,
        business_usage_name: businessUsage
      },
      user_id
    );
  }

  onResetPin() {
    const { selectedUser } = this.props;
    window.confirm(
      `Are you sure you wish to reset ${selectedUser.first_name} ${selectedUser.last_name}'s PIN?`
    ) && this.props.resetPin({ user_id: this.props.selectedUser.id });
  }

  onDeleteUser() {
    const { selectedUser } = this.props;
    let del = window.prompt(
      `Are you sure you wish to delete user "${selectedUser.first_name} ${selectedUser.last_name}"? This action cannot be undone. Type DELETE to confirm`
    );
    if (del === "DELETE") {
      this.props.deleteUser(selectedUser.id);
    } else {
      this.props.addMsg("Action Canceled");
    }
  }

  render() {
    return (
      <EditUserForm
        users={this.props.users}
        selectedUser={this.props.selectedUser}
        transferUsages={this.props.transferUsages}
        onSubmit={(form: IEditUser) => this.onEditUser(form)}
        onResetPin={() => this.onResetPin()}
        onDeleteUser={() => this.onDeleteUser()}
      />
    );
  }
}

const mapStateToProps = (state: ReduxState, ownProps: any): StateProps => {
  return {
    users: state.users,
    selectedUser: state.users.byId[parseInt(ownProps.userId)],
    transferUsages: state.transferUsages.transferUsages
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    editUser: (body, path) => dispatch(editUser({ body, path })),
    resetPin: body => dispatch(resetPin({ body })),
    deleteUser: path => dispatch(deleteUser({ path })),
    addMsg: msg =>
      dispatch(MessageAction.addMessage({ error: true, message: msg }))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(SingleUserManagement);
