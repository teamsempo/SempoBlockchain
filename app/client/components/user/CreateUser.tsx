import React  from 'react';
import { connect } from 'react-redux';

import { createUser, RESET_CREATE_USER } from '../../reducers/userReducer'
import { StyledButton, ModuleHeader } from '../styledElements'
import styles from './styles.module.css';
import CreateUserForm, {ICreateUser} from './CreateUserForm';
import CreateVendorForm, {ICreateVendor} from './CreateVendorForm';

//TODO(ts): fix types
interface DispatchProps {
  createUser: (body: any) => void,
  resetCreateUser: () => void
}

interface StateProps {
  users: any
}

interface OuterProps {
  isVendor: boolean
}

declare global {
  interface Window {
    BENEFICIARY_TERM: string
    IS_USING_BITCOIN: boolean
    MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT: number
    CURRENCY_NAME: string
  }
}

type Form = ICreateUser & ICreateVendor
type Props = DispatchProps & StateProps & OuterProps

class CreateUser extends React.Component<Props> {
  componentWillUnmount() {
      this.resetCreateUser()
  }

  resetCreateUser() {
    this.props.resetCreateUser();
  }

  onCreateUser(form: Form) {
    let publicSerialNumber;
    let phone;

    if (!form.publicSerialNumber) {
      publicSerialNumber = null;
      phone = null;
    } else if (form.publicSerialNumber.length < 7 || form.publicSerialNumber.match(/[a-z]/i)) {
      publicSerialNumber = form.publicSerialNumber;
      phone = null
    } else {
      publicSerialNumber = null;
      phone = form.publicSerialNumber;
    }

    this.props.createUser({
      first_name: form.firstName,
      last_name: form.lastName,
      bio: form.bio,
      gender: form.gender,
      public_serial_number: publicSerialNumber,
      phone: phone,
      blockchain_address: form.blockchainAddress,
      is_vendor: this.props.isVendor,
      custom_initial_disbursement: (form.customInitialDisbursement || 0) * 100,
      require_transfer_card_exists: true,
      existing_vendor_phone: form.existingVendorPhone,
      existing_vendor_pin: form.existingVendorPin,
      transfer_account_name: form.transferAccountName,
      location: form.location,
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
          onSubmit={(form: Form) => this.onCreateUser(form)}
        />
      }
    }
  }
}

const mapStateToProps = (state: any) => {
  return {
    users: state.users
  };
};

const mapDispatchToProps = (dispatch: any) => {
  return {
    createUser: (body: any) => dispatch(createUser({body})),
    resetCreateUser: () => {dispatch({type: RESET_CREATE_USER})},
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(CreateUser);

