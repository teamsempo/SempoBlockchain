import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import {
  loadBusinessProfile, RESET_ACTIVE_STEP_STATE, RESET_BUSINESS_VERIFICATION_STATE, UPDATE_ACTIVE_STEP
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

const mapDispatchToProps = (dispatch, ownProps) => {
  return {
    loadBusinessProfile: (query) => dispatch(loadBusinessProfile({query})),
    clearUserId: () => dispatch({type: RESET_ACTIVE_STEP_STATE}),
    clearBusienssState: () => dispatch({type: RESET_BUSINESS_VERIFICATION_STATE}),
    nextStep: () => dispatch({type: UPDATE_ACTIVE_STEP, activeStep: 0, userId: ownProps.userId})
  };
};

class GetVerified extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentWillMount() {
    const { userId } = this.props;
    this.props.clearUserId({'userId': userId});
    this.props.clearBusienssState();
  }

  componentDidMount() {
    const { userId } = this.props;
    let query;
    if (userId) {
      query = {'user_id': userId}
    }
    this.props.loadBusinessProfile(query)
  }

  render() {
    let { loadStatus, businessProfile, adminTier, userId } = this.props;
    var iconColor = '#ff1705';
    var text = 'Please contact support.';
    var addFunds = null;

    if (loadStatus.isRequesting) {
      return (
        <WrapperDiv>
          <LoadingSpinner/>
        </WrapperDiv>
      )
    }

    if (businessProfile.kyc_status === 'INCOMPLETE' || (!Object.values(businessProfile).length > 0)) {
      if (adminTier === 'superadmin') {
        text = <Link to='settings/verification'>Get Verified</Link>
      }

      if (userId) {
        text = <Link to={`/users/${userId}/verification`} onClick={this.props.nextStep.bind(this)}>Add User KYC</Link>
      }
    }

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