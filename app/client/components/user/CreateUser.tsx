import * as React  from 'react';
import { connect } from 'react-redux';

import { createUser, RESET_CREATE_USER } from '../../reducers/userReducer'
import { StyledButton, ModuleHeader } from '../styledElements'
import * as styles from './styles.module.css';
import { loadTransferUsages } from '../../reducers/transferUsage/actions'
import {TransferUsage} from "../../reducers/transferUsage/types";
import {Organisation} from "../../reducers/organisation/types";
import {ReduxState} from "../../reducers/rootReducer";
import {loadOrganisation} from "../../reducers/organisation/actions";
import CreateUserForm, {ICreateUserUpdate} from './CreateUserForm';
import {SignUpMethods} from "./signUpMethods";

interface DispatchProps {
  createUser: (body: any) => void,
  resetCreateUser: () => void
  loadTransferUsages: () => void
  loadOrganisation: () => void
}

interface StateProps {
  login: any,
  users: any,
  transferUsages: TransferUsage[]
  organisation?: Organisation
}

interface OuterProps {
  isVendor: boolean
}

declare global {
  interface Window {
    BENEFICIARY_TERM: string
    DEFAULT_INITIAL_DISBURSEMENT: number
  }
}

type Form = ICreateUserUpdate
type Props = DispatchProps & StateProps & OuterProps

class CreateUserUpdated extends React.Component<Props> {

  componentDidMount() {
    this.props.loadTransferUsages();
    this.props.loadOrganisation();
  }

  componentWillUnmount() {
      this.resetCreateUser()
  }

  resetCreateUser() {
    this.props.resetCreateUser();
  }

  onCreateUser(form: Form) {
    let businessUsage = form.businessUsage;
    if (businessUsage && businessUsage.toLowerCase() === "other") {
      businessUsage = form.usageOtherSpecific;
    }

    this.props.createUser({
      first_name: form.firstName,
      last_name: form.lastName,
      bio: form.bio,
      gender: form.gender,
      public_serial_number: form.publicSerialNumber,
      phone: form.phone,
      is_vendor: (form.accountType === 'vendor' || form.accountType === 'cashier'),
      is_tokenagent: form.accountType === 'tokenagent',
      is_groupaccount: form.accountType === 'groupaccount',
      initial_disbursement: (form.initialDisbursement || 0) * 100,
      require_transfer_card_exists: this.props.login.requireTransferCardExists,
      existing_vendor_phone: form.existingVendorPhone,
      existing_vendor_pin: form.existingVendorPin,
      transfer_account_name: form.transferAccountName,
      location: form.location,
      business_usage_name: businessUsage,
      referred_by: form.referredBy,
      sign_up_method: SignUpMethods.WEB_SIGNUP
    })
  }

  render() {
    const transferAccountType = this.props.isVendor ? "vendor" : window.BENEFICIARY_TERM.toLowerCase();
    const {one_time_code, is_external_wallet} = this.props.users.createStatus;

    if (one_time_code !== null) {
      if (is_external_wallet === true) {
        return (
          <div>
            <ModuleHeader>Successfully Created External Wallet User</ModuleHeader>
            <div style={{padding: '0 1em 1em'}}>

              <p>You can now send funds to the {transferAccountType}'s wallet.</p>

              <StyledButton onClick={() => this.resetCreateUser()}>
                Add another {transferAccountType}
              </StyledButton>
            </div>
          </div>
        )
      } else {
        return (
          <div>
            <ModuleHeader>One Time Code</ModuleHeader>
            <div style={{padding: '0 1em 1em'}}>
              <p className={styles.code}>{this.props.users.createStatus.one_time_code}</p>

              <p>Show the {transferAccountType} their one time code now. They will be able to instantly and securely log in via the android app.</p>

              <StyledButton onClick={() => this.resetCreateUser()}>
                Add another {transferAccountType}
              </StyledButton>
            </div>
          </div>
        )
      }
    } else {
      return <CreateUserForm
        users={this.props.users}
        transferAccountType={transferAccountType}
        transferUsages={this.props.transferUsages}
        onSubmit={(form: Form) => this.onCreateUser(form)}
      />;
    }
  }
}

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    login: state.login,
    users: state.users,
    transferUsages: state.transferUsages.transferUsages
  };
};

const mapDispatchToProps = (dispatch: any) => {
  return {
    createUser: (body: any) => dispatch(createUser({body})),
    resetCreateUser: () => {dispatch({type: RESET_CREATE_USER})},
    loadTransferUsages: () => {dispatch(loadTransferUsages())},
    loadOrganisation: () => {dispatch(loadOrganisation())}
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(CreateUserUpdated);

