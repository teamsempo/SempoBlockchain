import * as React  from 'react';
import { connect } from 'react-redux';

import {editUser, resetPin} from '../../reducers/userReducer'
import {TransferUsage} from "../../reducers/transferUsage/types";
import {ReduxState} from "../../reducers/rootReducer";
import EditUserForm, {ICreateUserUpdate} from './EditUserForm';

interface DispatchProps {
  editUser: (body: any, path: any) => void,
  resetPin: (body: any) => void
}

interface StateProps {
  users: any,
  selectedUser: any,
  transferUsages: TransferUsage[]
}

interface OuterProps {
  userId: number
}

type Form = ICreateUserUpdate
type Props = DispatchProps & StateProps & OuterProps

interface attr_dict {
  [key: string]: any
}

class SingleUserManagement extends React.Component<Props> {
  onEditUser(form: Form) {
    const single_transfer_account_id = this.props.userId.toString();
    const { selectedUser } = this.props;

    let businessUsage = form.businessUsage;
    if (businessUsage && businessUsage.toLowerCase() === "other") {
      businessUsage = form.usageOtherSpecific;
    }

    let custom_attr_keys = selectedUser && Object.keys(selectedUser.custom_attributes);
    let attr_dict = {};
    custom_attr_keys.map(key => {
      (attr_dict as attr_dict)[key] = form[key];
      return attr_dict
    });

    this.props.editUser({
      first_name: form.firstName,
      last_name: form.lastName,
      public_serial_number: form.publicSerialNumber,
      phone: form.phone,
      location: form.location,
      is_vendor: (form.accountType === 'vendor' || form.accountType === 'cashier'),
      is_tokenagent: form.accountType === 'tokenagent',
      is_groupaccount: form.accountType === 'groupaccount',
      referred_by: form.referredBy,
      custom_attributes: attr_dict,
      business_usage_name: businessUsage,
      },
      single_transfer_account_id
    );
  }

  onResetPin() {
    const { selectedUser } = this.props;
    window.confirm(`Are you sure you wish to reset ${selectedUser.first_name} ${selectedUser.last_name}'s PIN?`) &&
    this.props.resetPin({user_id: this.props.selectedUser.id})
  }

  render() {
    return <EditUserForm
      users={this.props.users}
      selectedUser={this.props.selectedUser}
      transferUsages={this.props.transferUsages}
      onSubmit={(form: Form) => this.onEditUser(form)}
      onResetPin={() => this.onResetPin()}
    />;
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
    editUser: (body, path) => dispatch(editUser({body, path})),
    resetPin: (body) => dispatch(resetPin({body})),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(SingleUserManagement);
