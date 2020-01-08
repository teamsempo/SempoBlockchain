import React from 'react';
import styled from 'styled-components';
import { connect } from 'react-redux';

import {StyledButton, StyledSelect, ModuleBox} from '../styledElements'
import AsyncButton from './../AsyncButton.jsx'

import { createTransferRequest } from '../../reducers/creditTransferReducer'

const mapStateToProps = (state) => {
  return {
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
    login: state.login
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    createTransferRequest: (body) => dispatch(createTransferRequest({body})),
  };
};

class NewTransferManager extends React.Component {
  constructor() {
    super();
    this.state = {
        action: 'select',
        create_transfer_type: 'DISBURSEMENT',
        transfer_amount: '',

    };
    this.handleChange = this.handleChange.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.createNewTransfer = this.createNewTransfer.bind(this);
  }

  handleChange (evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  handleClick() {
    this.setState(prevState => ({
      newTransfer: !prevState.newTransfer
    }));
  }

  createNewTransfer() {
      if (this.state.transfer_amount > 0) {
          var transfer_type = this.state.create_transfer_type;

          var recipient_transfer_account_id = null;
          var sender_transfer_account_id = null;
          var transfer_amount = null;
          var target_balance = null;

          if (this.props.transfer_account_ids.length > 1) {
              // BULK TRANSFER
              var is_bulk = true;
              var recipient_transfer_accounts_ids = this.props.transfer_account_ids;

              if (transfer_type === 'DISBURSEMENT') {
                  transfer_amount = this.state.transfer_amount * 100;
              }

              if (transfer_type === 'BALANCE') {
                  target_balance = this.state.transfer_amount * 100;
              }

              if (transfer_type === 'RECLAMATION') {
                  transfer_amount = this.state.transfer_amount * 100;
              }

              this.props.createTransferRequest({
                  is_bulk,
                  recipient_transfer_accounts_ids,
                  transfer_amount,
                  target_balance,
                  transfer_type,
              });

          } else {
              // SINGLE TRANSFER
              if (transfer_type === 'DISBURSEMENT') {
                  recipient_transfer_account_id = this.props.transfer_account_ids[0];
                  transfer_amount = this.state.transfer_amount * 100;
              }

              if (transfer_type === 'RECLAMATION') {
                  sender_transfer_account_id = this.props.transfer_account_ids[0];
                  transfer_amount = this.state.transfer_amount * 100;
              }

              if (transfer_type === 'BALANCE') {
                  recipient_transfer_account_id = this.props.transfer_account_ids[0];
                  target_balance = this.state.transfer_amount * 100;
              }

              this.props.createTransferRequest({
                  recipient_transfer_account_id,
                  sender_transfer_account_id,
                  transfer_amount,
                  target_balance,
                  transfer_type,
              });
          }
      }
  }

  render() {

    if (this.props.login.usdToSatoshiRate) {
      let amount = Math.round(this.state.transfer_amount/this.props.login.usdToSatoshiRate*100) /100;
      var convertedBitcoin = (
        <div style={{marginLeft: '1em', width: '7em'}}>
          ({(amount == 0? '-': amount)} USD)
        </div>
      )
    } else {
      convertedBitcoin = null
    }

      return(
          <ModuleBox>
              <Wrapper>
                  <TopRow>
                      <StyledSelect style={{fontWeight: '400', margin: 'auto 1em', lineHeight: '25px', height: '25px'}} name="create_transfer_type" defaultValue={this.state.create_transfer_type}
                              onChange={this.handleChange}>
                        <option name="create_transfer_type" value="DISBURSEMENT">DISBURSEMENT</option>
                        <option name="create_transfer_type" value="BALANCE">BALANCE</option>
                        {
                          window.IS_USING_BITCOIN? null : <option name="create_transfer_type" value="RECLAMATION">RECLAMATION</option>
                        }
                      </StyledSelect>
                      <div style={{margin: '0.8em'}}>
                          <StyledButton onClick={() => this.props.cancelNewTransfer()} style={{fontWeight: '400', margin: '0em 0.5em', lineHeight: '25px', height: '25px'}}>Cancel</StyledButton>
                      </div>
                  </TopRow>
                  <div style={{margin: '1em 0'}}>
                      <Row style={{margin: '0em 1em'}}>
                          <SubRow style={{width: 'inherit'}}>
                            <ManagerInput
                                type="number"
                                name="transfer_amount"
                                placeholder="enter amount:"
                                value={this.state.transfer_amount}
                                onChange={this.handleChange}
                                style={{width:'7em', margin: '0'}}
                            />
                           {window.CURRENCY_NAME}
                           { convertedBitcoin}
                          </SubRow>
                          <SubRow style={{margin: '0 0 0 2em', width: 'inherit'}}>
                              <AsyncButton onClick={this.createNewTransfer} miniSpinnerStyle={{height: '10px', width: '10px'}} buttonStyle={{display: 'inline-flex', fontWeight: '400', margin: '0 0 5px 0', lineHeight: '25px', height: '25px'}} isLoading={this.props.creditTransfers.createStatus.isRequesting} buttonText={((this.state.create_transfer_type === 'BALANCE') ? 'SET ' : 'CREATE ') + this.state.create_transfer_type}/>
                          </SubRow>
                      </Row>
                  </div>
              </Wrapper>
          </ModuleBox>
      )
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(NewTransferManager);

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const TopRow = styled.div`
  display: flex;
  width: 100%;
  justify-content: space-between;
`;

const ButtonWrapper = styled.div`
  margin: auto 1em;
  @media (max-width: 767px) {
  margin: auto 1em;
  display: flex;
  flex-direction: column;
  }
`;

const Row = styled.div`
  display: flex;
  align-items: center;
  @media (max-width: 767px) {
  width: calc(100% - 2em);
  margin: 0 1em;
  flex-direction: column;
  align-items: end;
  }
`;

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
  margin-left: 0.5em;
  width: 50%;
  font-size: 15px;
  &:focus {
  border-color: #2D9EA0;
  }
`;