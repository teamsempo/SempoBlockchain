import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import {
  loadBusinessProfile,
} from "../reducers/businessVerificationReducer";

import LoadingSpinner from "./loadingSpinner.jsx";
import { Link } from "react-router-dom";

const mapStateToProps = (state) => {
  return {
    adminTier: state.login.adminTier,
    loadStatus: state.businessVerification.loadStatus,
    businessProfile: state.businessVerification.businessVerificationState,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadBusinessProfile: () => dispatch(loadBusinessProfile()),
  };
};

class GetVerified extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    this.props.loadBusinessProfile()
  }

  render() {
    let { loadStatus, businessProfile, adminTier } = this.props;
    var iconColor = '#ff1705';
    var text = 'Please contact support.';
    var addFunds = null;

    if (businessProfile.kyc_status !== 'INCOMPLETE' && typeof businessProfile.kyc_status !== 'undefined' && businessProfile.kyc_status !== null) {

      if (businessProfile.kyc_status === 'PENDING') {
        iconColor = '#FF9800';
        text = 'Pending.';
        addFunds = null;
      }

      if (businessProfile.kyc_status === 'VERIFIED') {
        iconColor = '#00C759';
        text = 'Verified.';
        addFunds = null;

        if (adminTier === 'superadmin' || adminTier === 'admin') {
          addFunds = <div><br/><Link to='settings/fund-wallet'>Add Funds</Link></div>
        }
      }

      return(
        <div style={{margin: '1em'}}>
          <StyledAccountWrapper>
            <StyledHeader>Account Status:</StyledHeader>
            <StyledContent backgroundColor={iconColor}>{text}</StyledContent>
            {addFunds}
          </StyledAccountWrapper>
        </div>
      )
    }

    if (adminTier === 'superadmin') {
      text = <Link to='settings/verification'>Get Verified</Link>
    }

    if (loadStatus.isRequesting) {
      return (
        <WrapperDiv>
          <LoadingSpinner/>
        </WrapperDiv>
      )
    } else {
      return (
        <div style={{margin: '1em'}}>
          <StyledAccountWrapper>
            <StyledHeader>Account Status:</StyledHeader>
            <StyledContent backgroundColor={iconColor}>{text}</StyledContent>
          </StyledAccountWrapper>
        </div>
      )
    }
  }
}
export default connect(mapStateToProps, mapDispatchToProps)(GetVerified);

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const StyledHeader = styled.p`
  font-weight: 600;
  margin: 0 0 .6em;
`;

const StyledContent = styled.p`
  font-weight: 400;
  margin: 0;
  &:before {
  content: "\\2713";
  color: white;
  background-color: ${props => props.backgroundColor};
  width: 60px;
  font-size: 14px;
  border-radius: 1.2em;
  padding: 1px 5px;
  display: inline;
  margin-right: 10px;
  }
`;

const StyledAccountWrapper = styled.div`
  background-color: #f7fafc;
  padding: 1em;
  font-size: 14px;
  border: 1px solid #dbe4e8;
`;