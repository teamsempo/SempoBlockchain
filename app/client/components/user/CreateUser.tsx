import React  from 'react';
import { connect } from 'react-redux';

import { createUser, RESET_CREATE_USER } from '../../reducers/userReducer'
import { StyledButton, ModuleHeader } from '../styledElements'
import styles from './styles.module.css';
import CreateUserForm, {ICreateUser} from './CreateUserForm';
import CreateVendorForm, {ICreateVendor} from './CreateVendorForm';
import { loadTransferUsages } from '../../reducers/transferUsage/actions'
import {TransferUsage} from "../../reducers/transferUsage/types";
import {ReduxState} from "../../reducers/rootReducer";

interface DispatchProps {
  createUser: (body: any) => void,
  resetCreateUser: () => void
  loadTransferUsages: () => void
}

interface StateProps {
  users: any,
  transferUsages: TransferUsage[]
}

interface OuterProps {
  isVendor: boolean
}

declare global {
  interface Window {
    BENEFICIARY_TERM: string
    MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT: number
    CURRENCY_NAME: string
  }
}

type Form = ICreateUser & ICreateVendor
type Props = DispatchProps & StateProps & OuterProps

class CreateUser extends React.Component<Props> {
  componentDidMount() {
    this.props.loadTransferUsages();
  }

  componentWillUnmount() {
      this.resetCreateUser()
  }

  resetCreateUser() {
    this.props.resetCreateUser();
  }

  onCreateUser(form: Form) {
    this.props.createUser({
      first_name: form.firstName,
      last_name: form.lastName,
      bio: form.bio,
      gender: form.gender,
      public_serial_number: form.publicSerialNumber,
      phone: form.phone,
      is_vendor: this.props.isVendor,
      additional_initial_disbursement: (form.additionalInitialDisbursement || 0) * 100,
      //TODO(org): make this an organisation level field
      require_transfer_card_exists: true,
      existing_vendor_phone: form.existingVendorPhone,
      existing_vendor_pin: form.existingVendorPin,
      transfer_account_name: form.transferAccountName,
      location: form.location,
      business_usage_name: form.businessUsage,
      usage_other_specific: form.usageOtherSpecific
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
      if (this.props.isVendor) {
        return <CreateVendorForm
          users={this.props.users}
          transferAccountType={transferAccountType}
          onSubmit={(form: Form) => this.onCreateUser(form)}
        />
      } else {
        return <CreateUserForm
          users={this.props.users}
          transferAccountType={transferAccountType}
          transferUsages={this.props.transferUsages}
          onSubmit={(form: Form) => this.onCreateUser(form)}
        />
      }
    }
  }
}

//TODO: why doesn't ReduxState work correctly
const mapStateToProps = (state: any) => {
  return {
    users: state.users,
    transferUsages: state.transferUsages.transferUsages
  };
};

const mapDispatchToProps = (dispatch: any) => {
  return {
    createUser: (body: any) => dispatch(createUser({body})),
    resetCreateUser: () => {dispatch({type: RESET_CREATE_USER})},
    loadTransferUsages: () => {dispatch(loadTransferUsages())}
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(CreateUser);

