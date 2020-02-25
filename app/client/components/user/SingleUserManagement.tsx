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
  user: any,
  transferUsages: TransferUsage[]
}

interface OuterProps {
  userId: number
}

type Form = ICreateUserUpdate
type Props = DispatchProps & StateProps & OuterProps

class SingleUserManagement extends React.Component<Props> {

  onEditUser(form: Form) {
    const single_transfer_account_id = this.props.userId.toString();
    // const { custom_attr_keys } = this.state;

    let businessUsage = form.businessUsage;
    if (businessUsage && businessUsage.toLowerCase() === "other") {
      businessUsage = form.usageOtherSpecific;
    }

    //todo: get this working
    let attr_dict = {};
    // custom_attr_keys.map(key => {
    //   attr_dict[key] = this.state[key];
    //   return attr_dict
    // });

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

  onResetPin(form: Form) {
    window.confirm(`Are you sure you wish to reset ${form.firstName} ${form.lastName}'s PIN?`) &&
    this.props.resetPin({user_id: this.props.user.id})
  }

  render() {
    return <EditUserForm
      users={this.props.users}
      transferUsages={this.props.transferUsages}
      onSubmit={(form: Form) => this.onEditUser(form)}
      onResetPin={(form: Form) => this.onResetPin(form)}
    />;
  }
}

const mapStateToProps = (state: ReduxState, ownProps): StateProps => {
  return {
    users: state.users,
    user: state.users.byId[parseInt(ownProps.userId)],
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

