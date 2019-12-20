import React from 'react';
import { connect } from 'react-redux';
import styled, {ThemeProvider} from 'styled-components';

import {WrapperDiv, PageWrapper, ModuleHeader, ModuleBox, CenterLoadingSideBarActive } from '../styledElements';
import { LightTheme } from '../theme.js'

import {
  loadBusinessProfile,
  UPDATE_ACTIVE_STEP,
} from "../../reducers/businessVerificationReducer";

import BusinessDetails from '../verification/businessDetails.jsx';
import BusinessDocuments from '../verification/businessDocuments.jsx';
import BusinessBankLocation from '../verification/businessBankLocation.jsx';
import BusinessBankDetails from '../verification/businessBankDetails.jsx';
import BusinessBankDocuments from '../verification/businessBankDocuments.jsx';
import BusinessVerificationPending from '../verification/businessVerificationPending.jsx';

import LoadingSpinner from "../loadingSpinner.jsx";
import AsyncButton from "../AsyncButton.jsx";
import StepWizard from '../verification/stepWizard.jsx';

const mapStateToProps = (state) => {
  return {
    stepStatus: state.businessVerification.stepState,
    loadStatus: state.businessVerification.loadStatus,
    editStatus: state.businessVerification.editStatus,
    businessProfile: state.businessVerification.businessVerificationState,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadBusinessProfile: (query) => dispatch(loadBusinessProfile({query})),
    nextStep: () => dispatch({type: UPDATE_ACTIVE_STEP, activeStep: 0}),
  };
};

class BusinessVerificationPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    const { stepStatus, businessProfile } = this.props;
    let pathname_array = location.pathname.split('/').slice(1);
    let pathUserId = parseInt(pathname_array[1]);
    let query;
    if (!Object.values(businessProfile).length > 0 || pathUserId) {
      // only load business profile if none exists
      if (stepStatus && stepStatus.userId) {
        query = {'user_id': stepStatus.userId }
      } else {
        query = {'user_id': pathUserId }
      }
      this.props.loadBusinessProfile(query)
    }
  }

  render() {
    let { loadStatus, businessProfile, stepStatus } = this.props;

    const steps = [
      {name: 'Account Details', component: <BusinessDetails/>},
      {name: 'Documents', component: <BusinessDocuments/>},
      {name: 'Bank Location', component: <BusinessBankLocation/>},
      {name: 'Bank Details', component: <BusinessBankDetails/>},
      {name: 'Bank Documents', component: <BusinessBankDocuments/>},
      {name: 'Pending Verification', component: <BusinessVerificationPending/>}
    ];

    if (businessProfile.kyc_status === 'VERIFIED') {
      return(
        <WrapperDiv>
          <PageWrapper style={{display: 'flex', flexDirection: 'column'}}>
            <ModuleBox>
              <ModuleHeader>ACCOUNT STATUS</ModuleHeader>
              <p style={{margin: '1em'}}>You have been successfully verified!</p>
            </ModuleBox>
          </PageWrapper>
        </WrapperDiv>
      )
    }

    if (loadStatus.isRequesting) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner/>
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      )
    } else if (stepStatus.activeStep >= 0 || Object.values(businessProfile).length > 0) {

      return (
        <WrapperDiv>
          <PageWrapper style={{display: 'flex', flexDirection: 'column'}}>
            <ThemeProvider theme={LightTheme}>
              <div>
                <ModuleBox>
                  <ModuleHeader>Account Verification</ModuleHeader>

                  <StepWizard steps={steps} activeStep={stepStatus.activeStep}/>

                </ModuleBox>

              </div>
            </ThemeProvider>
          </PageWrapper>
        </WrapperDiv>
      );
    } else if (loadStatus.error) {
      return (
        <WrapperDiv>
          <PageWrapper style={{display: 'flex', flexDirection: 'column'}}>
            <div>
                <ModuleBox>
                  <ModuleHeader>Account Verification</ModuleHeader>

                  <div style={{margin: '1em'}}>

                    <p>You can't send money until you finish verifying your account.</p>

                    <p>In order to verify your account we will need:</p>

                    <ul>
                      <li>
                        Business Details
                      </li>
                      <li>
                        Business Documents (e.g. Incorporation, Beneficial Owner IDs)
                      </li>
                      <li>
                        Bank Account Details
                      </li>
                      <li>
                        Bank Account Documents (e.g. Statement)
                      </li>
                    </ul>

                    <AsyncButton buttonText={'Get Started'} onClick={this.props.nextStep}/>

                  </div>

                </ModuleBox>

              </div>
          </PageWrapper>
        </WrapperDiv>
      )
    } else {
      return (
        <WrapperDiv>
          <p>Something went wrong</p>
        </WrapperDiv>
      )
    }
  }
}
export default connect(mapStateToProps, mapDispatchToProps)(BusinessVerificationPage);