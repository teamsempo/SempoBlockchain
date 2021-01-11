import * as React from "react";
import { connect } from "react-redux";
import { message } from "antd";

import { TransferUsage } from "../../reducers/transferUsage/types";
import { ReduxState } from "../../reducers/rootReducer";
import EditUserForm, { IEditUser } from "./EditUserForm";
import {
  DeleteUserAction,
  EditUserAction,
  ResetPinAction
} from "../../reducers/user/actions";
import {
  User,
  ResetPinPayload,
  DeleteUserPayload
} from "../../reducers/user/types";

interface DispatchProps {
  editUser: (body: User, path: number) => EditUserAction;
  resetPin: (payload: ResetPinPayload) => ResetPinAction;
  deleteUser: (payload: DeleteUserPayload) => DeleteUserAction;
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
        account_types: form.accountTypes,
        referred_by: form.referredBy,
        custom_attributes: attr_dict,
        business_usage_name: businessUsage
      },
      this.props.userId
    );
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
      `Are you sure you wish to delete participant "${selectedUser.first_name} ${selectedUser.last_name}"? This action cannot be undone. Type DELETE to confirm`
    );
    if (del === "DELETE") {
      this.props.deleteUser({ path: selectedUser.id });
    } else {
      message.error("Action Canceled");
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
    editUser: (body: User, path: number) =>
      dispatch(EditUserAction.editUserRequest({ body, path })),
    resetPin: payload => dispatch(ResetPinAction.resetPinRequest(payload)),
    deleteUser: payload => dispatch(DeleteUserAction.deleteUserRequest(payload))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(SingleUserManagement);
