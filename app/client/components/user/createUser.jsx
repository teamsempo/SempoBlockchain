import React , { lazy }  from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import AsyncButton from '../AsyncButton.jsx'
import QrReadingModal from "../qrReadingModal.jsx"
// const QrReadingModal = lazy(() => import("../qrReadingModal.jsx"));


import { createUser, RESET_CREATE_USER } from '../../reducers/userReducer'

import { Input, StyledButton, ErrorMessage, ModuleHeader } from '../styledElements'

const mapStateToProps = (state) => {
  return {
    users: state.users
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    createUser: (body) => dispatch(createUser({body})),
    resetCreateUser: () => {dispatch({type: RESET_CREATE_USER})},
  };
};

class CreateUserForm extends React.Component {

  constructor(props) {
    super(props);
    this.state = this.initialState;

    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleCashierChange = this.handleCashierChange.bind(this);
  }

  initialState = {
    is_cashier_account: false,
    existing_vendor_phone: null,
    existing_vendor_pin: null,
    transfer_account_name: null,
    blockchain_adddress: null,
    first_name: null,
    last_name: null,
    phone: null,
    public_serial_number: null,
    custom_initial_disbursement: 0,
    location: null,
    error_message: null
  };

  componentWillUnmount() {
      this.resetCreateUser()
  }

  resetCreateUser() {
    this.props.resetCreateUser();
    this.setState(this.initialState)
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.type === 'checkbox' ? target.checked : target.value;
    const name = target.name;

    this.setState({
      [name]: value,
      error_message: ''
    });
  }

  handleCashierChange(event) {
    const target = event.target;

    this.setState({
      is_cashier_account: target.checked,
      first_name: target.checked? '' : this.state.first_name,
      last_name: target.checked? '' : this.state.last_name
    })
  }

  attemptCreateUser() {
    if (this.state.first_name === null && !this.state.is_cashier_account) {
      this.setState({error_message: 'Missing Name'});
      return
    }
    if (this.state.public_serial_number === null && this.state.blockchain_address === null) {
      this.setState(
        {error_message: window.IS_USING_BITCOIN? 'Missing Blockchain Address' : 'Missing Phone or ID'});
      return
    }

    if (!this.state.public_serial_number) {
      var public_serial_number = null;
      var phone = null;
    } else if (this.state.public_serial_number.length < 7 || this.state.public_serial_number.match(/[a-z]/i)) {
      public_serial_number = this.state.public_serial_number;
      phone = null
    } else {
      public_serial_number = null;
      phone = this.state.public_serial_number;
    }

    this.props.createUser({
      existing_vendor_phone: this.state.existing_vendor_phone,
      existing_vendor_pin: this.state.existing_vendor_pin,
      transfer_account_name: this.state.transfer_account_name,
      first_name: this.state.first_name,
      last_name: this.state.last_name,
      public_serial_number: public_serial_number,
      phone: phone,
      blockchain_address: this.state.blockchain_address,
      location: this.state.location,
      is_vendor: this.props.is_vendor,
      custom_initial_disbursement: this.state.custom_initial_disbursement * 100,
      require_transfer_card_exists: true
    })
  }


  render() {

    let {
      is_cashier_account,
      public_serial_number,
      blockchain_address,
      existing_vendor_phone,
      existing_vendor_pin,
      transfer_account_name,
      location,
      custom_initial_disbursement
    } = this.state;

    let {one_time_code, has_private_key} = this.props.users.createStatus;

    if (!window.IS_USING_BITCOIN) {
      var unique_indentifier_input = (
        <InputObject>
          <InputLabel>
            {is_cashier_account?
              'Cashier Phone Number' : 'Phone Number or ID'}:
          </InputLabel>
          <div style={{display: 'flex'}}>
            <ManagerInput
              name="public_serial_number"
              type="text"
              value={public_serial_number}
              onChange={this.handleInputChange} />

              <QrReadingModal
                updateData={
                  (data) => {
                    this.setState({
                      public_serial_number: data.replace(/^\s+|\s+$/g, '')
                    })
                  }
                }
              />

          </div>
        </InputObject>
      )
    } else {
      unique_indentifier_input = (
        <InputObject>
          <InputLabel>
            Bitcoin Address
          </InputLabel>
          <ManagerInput
            name="blockchain_address"
            type="text"
            value={blockchain_address}
            onChange={this.handleInputChange} />
        </InputObject>
      )
    }

    if (this.props.is_vendor){
      var transferAccountName = 'Vendor';

      var isCashierAccount = (
        <InputObject>
          <InputLabel>
            Create Cashier Account
          </InputLabel>
          <ManagerInput
            name="is_cashier_account"
            type="checkbox"
            checked={is_cashier_account}
            onChange={this.handleCashierChange} />
        </InputObject>
      );


      if (is_cashier_account) {
        var vendor_input = (
          <div>
            <div>
              To create a cashier account, enter the <b>vendor's</b> phone and pin.
            </div>
            <InputObject>
              <InputLabel>
                Vendor Phone Number:
              </InputLabel>
              <ManagerInput
                name="existing_vendor_phone"
                type="text"
                checked={existing_vendor_phone}
                onChange={this.handleInputChange} />
            </InputObject>

            <InputObject>
              <InputLabel>
                Vendor PIN:
              </InputLabel>
              <ManagerInput
                name="existing_vendor_pin"
                type="password"
                value={existing_vendor_pin}
                onChange={this.handleInputChange} />
            </InputObject>
          </div>
        )
      } else {
        vendor_input = (
        <div>
          <InputObject>
              <InputLabel>
                Store Name:
              </InputLabel>
              <ManagerInput
                name="transfer_account_name"
                type="text"
                value={transfer_account_name}
                onChange={this.handleInputChange} />
          </InputObject>

          <InputObject>
              <InputLabel>
                Address:
              </InputLabel>
              <ManagerInput
                name="location"
                type="test"
                value={location}
                onChange={this.handleInputChange} />
            </InputObject>
        </div>
        )
      }

      var initial_disbursement_amount = (<div></div>)
    } else {
      transferAccountName = window.BENEFICIARY_TERM.toLowerCase();

      isCashierAccount = (<div></div>);

      vendor_input = (<div></div>)

      if (window.MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT > 0) {
        initial_disbursement_amount = (
          <InputObject>
            <InputLabel>
              Initial Disbursement Amount:
            </InputLabel>
            <ManagerInput
              name="custom_initial_disbursement"
              type="number"
              value={custom_initial_disbursement}
              onChange={this.handleInputChange} />
            {window.CURRENCY_NAME}
          </InputObject>
        )
      } else {
        initial_disbursement_amount = (<div></div>)
      }


    }

    if (one_time_code !== null && has_private_key === true) {
      return (
          <div>
            <ModuleHeader>One Time Code</ModuleHeader>
            <div style={{padding: '0 1em 1em'}}>
              <Code>{this.props.users.createStatus.one_time_code}</Code>

              <p>Show the {transferAccountName} their one time code now. They will be able to instantly and securely log in via the android app.</p>

              <StyledButton onClick={() => this.resetCreateUser()}>
                Add another {transferAccountName}
              </StyledButton>
            </div>
          </div>
        )
    }

    if (one_time_code !== null && has_private_key === false) {
      return (
          <div>
            <ModuleHeader>Successfully Created External Wallet User</ModuleHeader>
            <div style={{padding: '0 1em 1em'}}>

              <p>You can now send funds to the {transferAccountName}'s wallet.</p>

              <StyledButton onClick={() => this.resetCreateUser()}>
                Add another {transferAccountName}
              </StyledButton>
            </div>
          </div>
        )
    }

    return (
      <div>
        <ModuleHeader>Create a {transferAccountName} account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form>

            {isCashierAccount}

            {vendor_input}

            <InputObject>
              <InputLabel>
                First Name:
              </InputLabel>
              <ManagerInput
                name="first_name"
                type="text"
                value={this.state.first_name}
                onChange={this.handleInputChange} />
            </InputObject>

            <InputObject>
              <InputLabel>
                Last Name:
              </InputLabel>
              <ManagerInput
                name="last_name"
                type="text"
                value={this.state.last_name}
                onChange={this.handleInputChange} />
            </InputObject>

            {unique_indentifier_input}

            {initial_disbursement_amount}

            {/*<InputObject>*/}
              {/*Account Number:*/}
              {/*<ManagerInput*/}
                {/*name="public_serial_number"*/}
                {/*type="text"*/}
                {/*value={this.state.public_serial_number}*/}
                {/*onChange={this.handleInputChange} />*/}
            {/*</InputObject>*/}


            <ErrorMessage>
              {this.state.error_message}{this.props.users.createStatus.error}
            </ErrorMessage>

          </form>

          <AsyncButton
              onClick={() => this.attemptCreateUser()}
              isLoading={this.props.users.createStatus.isRequesting}
              buttonStyle={{display: 'flex'}}
              buttonText="Submit"
          />

        </div>

      </div>

    );
  }

}

export default connect(mapStateToProps, mapDispatchToProps)(CreateUserForm);

const SubRow = styled.div`
  display: flex;
  align-items: center;
  width: 33%;
  @media (max-width: 767px) {
  width: 100%;
  justify-content: space-between;
  }
`;

const ManagerInput = styled.input`
  color: #555;
  border: solid #d8dbdd;
  border-width: 0 0 1px 0;
  outline: none;
  max-width: 300px;
  font-size: 18px;
  &:focus {
  border-color: #2D9EA0;
  }
`;

const InputObject = styled.label`
  display:block;
  padding: 1em;
  font-size: 15px;
`;

const InputLabel = styled.div`
  display:block;
  font-size: 14px;
`

const Code = styled.p`
  text-align: center;
  font-size: 3em;
  font-weight: 700;
`;