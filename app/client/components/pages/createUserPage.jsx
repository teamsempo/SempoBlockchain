import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import SideBar from '../navBar.jsx'
import {PageWrapper, ModuleBox} from '../styledElements.js'
import CreateTransferAccount from '../user/createUser.jsx'
import UploadButton from '../uploader/uploadButton.jsx';
import {StyledSelect} from "../styledElements";

const mapStateToProps = (state) => {
  return {
    loggedIn: (state.login.userId != null),
  };
};

class createUserPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      account_type: window.BENEFICIARY_TERM
    };
    this.handleChange = this.handleChange.bind(this);
  }

  handleChange (evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  render() {
    const is_vendor = this.state.account_type === 'VENDOR';

    return (
        <WrapperDiv>
          <SideBar/>

          <PageWrapper>
              <ModuleBox>
                <div style={{display: 'flex', flexDirection: 'row', borderBottom: 'solid #00000020', borderBottomWidth: '1px', margin: '0 1em'}}>
                  <p>Account Type:</p>
                  <StyledSelect style={{fontWeight: '400', margin: '1em', lineHeight: '25px', height: '25px'}} name="account_type" value={this.state.account_type} onChange={this.handleChange}>
                    <option name="account_type" value={window.BENEFICIARY_TERM}>{window.BENEFICIARY_TERM}</option>
                    <option name="account_type" value="VENDOR">VENDOR</option>
                  </StyledSelect>
                </div>
                <CreateTransferAccount is_vendor={is_vendor}/>
              </ModuleBox>
              <p style={{textAlign: 'center'}}>or</p>
              <UploadButtonWrapper style={{marginLeft: 0}}>
                <UploadButton button={true} uploadButtonText="Upload Spreadsheet" is_vendor={is_vendor} />
              </UploadButtonWrapper>
          </PageWrapper>
        </WrapperDiv>

    );

  }
}

export default connect(mapStateToProps, null)(createUserPage);

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const UploadButtonWrapper = styled.div`
  display: flex;
  justify-content: center;
  margin: auto 1em;
  @media (max-width: 767px) {
  //overflow: hidden;
  //text-overflow: ellipsis;
  //box-shadow: 0px 2px 0px 0 rgba(51,51,79,.08);
  }
`;