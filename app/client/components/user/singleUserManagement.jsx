import React from 'react';
import styled from 'styled-components';
import { connect } from 'react-redux';
import { Link } from 'react-router-dom';

import { replaceUnderscores } from "../../utils";

import { ModuleBox, ModuleHeader } from '../styledElements'
import AsyncButton from './../AsyncButton.jsx'
import ProfilePicture from '../profilePicture.jsx'

import { editUser } from '../../reducers/userReducer'
import { formatMoney } from "../../utils";
import QrReadingModal from "../qrReadingModal.jsx";

const mapStateToProps = (state, ownProps) => {
  return {
    users: state.users,
    user: state.users.byId[parseInt(ownProps.user_id)]
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    editUser: (body, path) => dispatch(editUser({body, path})),
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
    };
    this.handleChange = this.handleChange.bind(this);
    this.onSave = this.onSave.bind(this);
  }

  componentDidMount() {
      const { user } = this.props;

      if (user !== null) {
          this.setState({
              first_name: user.first_name,
              last_name: user.last_name,
              nfc_serial_number: user.nfc_serial_number,
              public_serial_number: user.public_serial_number,
              phone: user.phone,
              location: user.location
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

    const single_transfer_account_id = this.props.user_id.toString();

    this.props.editUser(
        {
            first_name,
            last_name,
            nfc_serial_number,
            public_serial_number,
            phone,
            location,
        },
        single_transfer_account_id
    );
  }

  handleChange (evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  onSave() {
      this.editUser();
  }

  render() {
    let blockchain_address = '';
    if (this.props.user.transfer_account) {
      blockchain_address =  this.props.user.transfer_account.blockchain_address.address
      if (!window.IS_USING_BITCOIN) {
        var tracker_link = (
          'https://' + window.ETH_CHAIN_NAME  +  (window.ETH_CHAIN_NAME? '.':'')
          + 'etherscan.io/address/' + blockchain_address
        )
      } else {
        tracker_link = (
          'https://www.blockchain.com/' + (window.IS_BITCOIN_TESTNET? 'btctest' : 'btc') +
          '/address/' + blockchain_address
        )
      }
    }




    if (this.props.user.custom_attributes.profile_picture) {

      console.log(this.props.user.custom_attributes.profile_picture);

      if (this.props.user.custom_attributes.profile_picture.roll) {
        var quantised_roll = Math.floor(this.props.user.custom_attributes.profile_picture.roll/90 + 0.5) * -90
      } else {
        quantised_roll = 0
      }
      var profilePicture = (
        <ProfilePicture
          label={"Profile Picture:"}
          roll={this.props.user.custom_attributes.profile_picture.roll}
          url={this.props.user.custom_attributes.profile_picture.url}
        />
      )
    } else {
      profilePicture = null
    }

    if (this.props.user.matched_profile_pictures.length > 0) {
      var matched_profiles = this.props.user.matched_profile_pictures.map(match => (
        <Link to={"/users/" + match.user_id}
              key={match.user_id}
              style={{
                color: 'inherit',
                textDecoration: 'inherit',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center'}}>

          <ProfilePicture
            label={"Possible Duplicate User:"}
            sublabel ={'User ' + match.user_id}
            roll={match.roll}
            url={match.url}
          />

        </Link>
        )
      )
    } else {
      matched_profiles = null
    }

    console.log(this.props.user.custom_attributes);

    var custom_attribute_list = Object.keys(this.props.user.custom_attributes).map( key =>
      {
        if (!this.props.user.custom_attributes[key].uploaded_image_id) {
          return (
            <SubRow key={key}>
              <InputLabel>{replaceUnderscores(key)}: </InputLabel>
              <div style={{marginLeft: '0.5em', marginRight: '4em'}}>
                {replaceUnderscores(this.props.user.custom_attributes[key].value)}
              </div>
            </SubRow>
          )
        }
      }
    );

      return (
          <div style={{display: 'flex', flexDirection: 'column'}}>

              <ModuleBox>
                  <Wrapper>
                      <TopRow>
                          <ModuleHeader>DETAILS</ModuleHeader>
                          <ButtonWrapper>
                            <AsyncButton onClick={this.onSave} miniSpinnerStyle={{height: '10px', width: '10px'}} buttonStyle={{display: 'inline-flex', fontWeight: '400', margin: '0em', lineHeight: '25px', height: '25px'}} isLoading={this.props.users.editStatus.isRequesting} buttonText="SAVE"/>
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
                            {blockchain_address.substring(window.IS_USING_BITCOIN? 0:2,)}
                            </a>
                          </ManagerText>
                        </SubRow>
                      </Row>
                      <Row style={{margin: '0em 1em', flexWrap: 'wrap'}}>
                        {custom_attribute_list}
                      </Row>
                      <Row style={{margin: '0em 1em'}}>
                        <SubRow>
                        { profilePicture }
                        </SubRow>
                        <SubRow>
                        { matched_profiles }
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