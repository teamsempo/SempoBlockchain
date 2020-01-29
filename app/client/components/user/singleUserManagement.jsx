import React from 'react';
import styled from 'styled-components';
import { connect } from 'react-redux';
import { Link } from 'react-router-dom';

import { replaceUnderscores } from "../../utils";

import {ModuleBox, ModuleHeader, StyledSelect} from '../styledElements'
import AsyncButton from './../AsyncButton.jsx'
import ProfilePicture from '../profilePicture.jsx'
import GetVerified from '../GetVerified.jsx'

import {editUser, resetPin} from '../../reducers/userReducer'
import QrReadingModal from "../qrReadingModal.jsx";

import {TransferAccountTypes} from "../transferAccount/types";

const mapStateToProps = (state, ownProps) => {
  return {
    users: state.users,
    user: state.users.byId[parseInt(ownProps.userId)]
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    editUser: (body, path) => dispatch(editUser({body, path})),
    resetPin: (body) => dispatch(resetPin({body})),
  };
};

class SingleUserManagement extends React.Component {
  constructor() {
    super();
    this.state = {
      first_name: '',
      last_name: '',
      nfc_serial_number: '',
      public_serial_number: '',
      phone: '',
      location: '',
      account_type: '',
    };
    this.handleChange = this.handleChange.bind(this);
  }

  componentDidMount() {
    const { user } = this.props;
    let account_type;

    if (user !== null) {
      if (user.is_beneficiary) {
        account_type = TransferAccountTypes.USER
      } else if (user.is_vendor) {
        account_type = TransferAccountTypes.VENDOR
      } else if (user.is_tokenagent) {
        account_type = TransferAccountTypes.TOKENAGENT
      } else if (user.is_groupaccount) {
        account_type = TransferAccountTypes.GROUPACCOUNT
      }


      this.setState({
        first_name: user.first_name,
        last_name: user.last_name,
        nfc_serial_number: user.nfc_serial_number,
        public_serial_number: user.public_serial_number,
        phone: user.phone,
        location: user.location,
        account_type: account_type
      });
    }
  }

  editUser() {
    const first_name = this.state.first_name;
    const last_name = this.state.last_name;
    const nfc_serial_number = this.state.nfc_serial_number;
    const public_serial_number = this.state.public_serial_number;
    const phone = this.state.phone;
    const location = this.state.location;
    const account_type = this.state.account_type;

    const single_transfer_account_id = this.props.userId.toString();

    this.props.editUser({
        first_name,
        last_name,
        nfc_serial_number,
        public_serial_number,
        phone,
        location,
        is_vendor: (account_type === 'VENDOR' || account_type === 'CASHIER'),
        is_tokenagent: account_type === 'TOKENAGENT',
        is_groupaccount: account_type === 'GROUPACCOUNT',
        },
        single_transfer_account_id
    );
  }

  handleChange (evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  resetPin() {
    window.confirm(`Are you sure you wish to reset ${this.state.first_name} ${this.state.last_name}'s PIN?`) &&
    this.props.resetPin({user_id: this.props.user.id})
  }

  render() {
    let accountTypes = Object.keys(TransferAccountTypes);
    let blockchain_address = '';
    if (this.props.user.transfer_account) {
      blockchain_address =  this.props.user.transfer_account.blockchain_address;
      var tracker_link = window.ETH_EXPLORER_URL + '/address/' + blockchain_address;
    }

    var profilePicture = null;
    var custom_attribute_list = null;
    if (this.props.user.custom_attributes !== null && typeof this.props.user.custom_attributes !== "undefined") {

      if (this.props.user.custom_attributes.profile_picture) {
        profilePicture = (
          <ProfilePicture
            label={"Profile Picture:"}
            roll={this.props.user.custom_attributes.profile_picture.roll}
            url={this.props.user.custom_attributes.profile_picture.url}
          />
        )
      } else {
        profilePicture = null
      }

      custom_attribute_list = Object.keys(this.props.user.custom_attributes).map(key => {
          if (!this.props.user.custom_attributes[key].uploaded_image_id) {
            return (
              <SubRow key={key}>
                <InputLabel>{replaceUnderscores(key)}: </InputLabel>
                <div style={{marginLeft: '0.5em', marginRight: '4em'}}>
                  {replaceUnderscores(this.props.user.custom_attributes[key])}
                </div>
              </SubRow>
            )
          }
        }
      );
    }

      return (
          <div style={{display: 'flex', flexDirection: 'column'}}>

              <ModuleBox>
                  <Wrapper>
                      <TopRow>
                          <ModuleHeader>DETAILS</ModuleHeader>
                          <ButtonWrapper>
                            <AsyncButton onClick={this.editUser.bind(this)} miniSpinnerStyle={{height: '10px', width: '10px'}} buttonStyle={{display: 'inline-flex', fontWeight: '400', margin: '0em', lineHeight: '25px', height: '25px'}} isLoading={this.props.users.editStatus.isRequesting} buttonText="SAVE"/>
                          </ButtonWrapper>
                      </TopRow>
                      <Row style={{margin: '0em 1em'}}>
                          <SubRow>
                              <InputLabel>First Name: </InputLabel><ManagerInput name="first_name" placeholder="n/a" value={this.state.first_name || ''} onChange={this.handleChange}/>
                          </SubRow>
                          <SubRow>
                              <InputLabel>Last Name: </InputLabel><ManagerInput name="last_name" placeholder="n/a" value={this.state.last_name || ''} onChange={this.handleChange}/>
                          </SubRow>
                          <SubRow>
                              <InputLabel>Phone: </InputLabel><ManagerInput name="phone" placeholder="n/a" value={this.state.phone || ''} onChange={this.handleChange}/>
                          </SubRow>
                      </Row>
                      <Row style={{margin: '0em 1em'}}>
                        <SubRow>
                          <InputLabel>Public serial number: </InputLabel>
                          <div style={{display: 'flex'}}>
                            <ManagerInput name="public_serial_number" placeholder="n/a" value={this.state.public_serial_number || ''} onChange={this.handleChange}/>
                            <QrReadingModal
                              updateData={
                                (data) => {
                                  let public_serial_number = data.replace(/^\s+|\s+$/g, '');
                                  this.setState({public_serial_number})
                                }
                              }
                            />
                          </div>
                        </SubRow>
                        <SubRow>
                          <InputLabel>Location: </InputLabel>
                          <ManagerInput name="location" placeholder="n/a" value={this.state.location || ''} onChange={this.handleChange}/>
                        </SubRow>
                        <SubRow>
                          <InputLabel>User Type: </InputLabel>
                          <StyledSelect style={{fontWeight: '400', margin: '1em', lineHeight: '25px', height: '25px'}} name="account_type" value={this.state.account_type} onChange={this.handleChange}>
                            {accountTypes.map((accountType, index) => {
                              return <option key={index} name="account_type" value={accountType}>{accountType}</option>
                            })}
                          </StyledSelect>
                        </SubRow>
                      </Row>
                      <Row style={{margin: '0em 1em'}}>
                        {
                          (this.props.user.one_time_code !== '') ?
                            <SubRow>
                              <InputLabel>One Time Code:</InputLabel><ManagerText>{this.props.user.one_time_code}</ManagerText>
                            </SubRow>
                            :
                            null
                        }

                        <SubRow>
                          <InputLabel>Blockchain Address: </InputLabel>
                          <ManagerText>
                            <a  href={tracker_link}
                                     target="_blank">
                            {blockchain_address.substring(2,)}
                            </a>
                          </ManagerText>
                        </SubRow>

                        <SubRow style={{margin: '-1em -1em 0'}}>
                          <GetVerified userId={this.props.userId}/>
                        </SubRow>

                      </Row>
                    <Row style={{margin: '0em 1em'}}>
                      <SubRow>
                        <InputLabel>Failed Pin Attempts:</InputLabel>
                        <ManagerText>
                          {this.props.user.failed_pin_attempts}
                          {this.props.user.failed_pin_attempts === 3 ? " (BLOCKED)" : ""}
                        </ManagerText>
                        <AsyncButton onClick={this.resetPin.bind(this)}
                                     miniSpinnerStyle={{height: '10px', width: '10px'}}
                                     buttonStyle={{display: 'inline-flex', fontWeight: '400', margin: '0em', lineHeight: '25px', height: '25px'}}
                                     isLoading={this.props.users.pinStatus.isRequesting}
                                     buttonText="Reset Pin"/>
                      </SubRow>
                    </Row>
                      <Row style={{margin: '0em 1em', flexWrap: 'wrap'}}>
                        {custom_attribute_list || null}
                      </Row>
                      <Row style={{margin: '0em 1em'}}>
                        <SubRow>
                        { profilePicture || null }
                        </SubRow>
                        <SubRow>
                        </SubRow>
                      </Row>
                  </Wrapper>
              </ModuleBox>
          </div>
      );
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(SingleUserManagement);

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

const InputLabel = styled.p`
  font-size: 15px;
  font-weight: 600;
  text-transform: capitalize;
`;

const ManagerText = styled.p`
  color: #555;
  margin-left: 0.5em;
  width: 50%;
  font-size: 15px;
`;