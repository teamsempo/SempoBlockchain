import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import {
  WrapperDiv,
  PageWrapper,
  ModuleHeader,
  ModuleBox,
  CenterLoadingSideBarActive,
  Row
} from "../styledElements";
import { LightTheme } from "../theme.js";

import { BusinessVerificationAction } from "../../reducers/businessVerification/actions";

import BusinessDetails from "../verification/businessDetails.jsx";
import BusinessDocuments from "../verification/businessDocuments.jsx";
import BusinessBankLocation from "../verification/businessBankLocation.jsx";
import BusinessBankDetails from "../verification/businessBankDetails.jsx";
import BusinessBankDocuments from "../verification/businessBankDocuments.jsx";
import BusinessVerificationPending from "../verification/businessVerificationPending.jsx";

import LoadingSpinner from "../loadingSpinner.jsx";
import AsyncButton from "../AsyncButton.jsx";
import StepWizard from "../verification/stepWizard.jsx";

const mapStateToProps = state => {
  return {
    stepStatus: state.businessVerification.stepState,
    loadStatus: state.businessVerification.loadStatus,
    editStatus: state.businessVerification.editStatus,
    businessProfile: state.businessVerification.businessVerificationState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadBusinessProfile: query =>
      dispatch(
        BusinessVerificationAction.loadBusinessVerificationRequest({ query })
      ),
    nextStep: () => dispatch(BusinessVerificationAction.updateActiveStep(0))
  };
};

class BusinessVerificationPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      userId: null,
      is_bank_account: true
    };
    this.handleInputChange = this.handleInputChange.bind(this);
  }

  componentWillMount() {
    const { stepStatus, businessProfile } = this.props;
    let pathname_array = location.pathname.split("/").slice(1);
    let pathUserId = parseInt(pathname_array[1]);
    let query;
    if (Object.values(businessProfile).length === 0 || pathUserId) {
      // only load business profile if none exists
      if (stepStatus && stepStatus.userId) {
        query = { user_id: stepStatus.userId };
        this.setState({ userId: stepStatus.userId });
      } else {
        query = { user_id: pathUserId };
        this.setState({ userId: pathUserId });
      }
      this.props.loadBusinessProfile(query);
    }
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.type === "checkbox" ? target.checked : target.value;
    const name = target.name;

    this.setState({
      [name]: value
    });
  }

  render() {
    let { loadStatus, businessProfile, stepStatus } = this.props;
    let { userId } = this.state;

    let finalSteps;
    const steps = [
      {
        name: "Account Details",
        component: <BusinessDetails userId={this.state.userId} />
      },
      {
        name: "Documents",
        component: <BusinessDocuments isFinal={!this.state.is_bank_account} />
      },
      { name: "Bank Location", component: <BusinessBankLocation /> },
      { name: "Bank Details", component: <BusinessBankDetails /> },
      { name: "Bank Documents", component: <BusinessBankDocuments /> },
      {
        name: "Pending Verification",
        component: <BusinessVerificationPending />
      }
    ];

    if (!this.state.is_bank_account) {
      steps.splice(2, 3);
      finalSteps = steps;
    } else {
      finalSteps = steps;
    }

    if (businessProfile.kyc_status === "VERIFIED") {
      return (
        <WrapperDiv>
          <PageWrapper style={{ display: "flex", flexDirection: "column" }}>
            <ModuleBox>
              <ModuleHeader>ACCOUNT STATUS</ModuleHeader>
              <p style={{ margin: "1em" }}>
                You have been successfully verified!
              </p>
            </ModuleBox>
          </PageWrapper>
        </WrapperDiv>
      );
    }

    if (loadStatus.isRequesting) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      );
    } else if (
      stepStatus.activeStep >= 0 ||
      Object.values(businessProfile).length > 0
    ) {
      return (
        <WrapperDiv>
          <PageWrapper style={{ display: "flex", flexDirection: "column" }}>
            <ThemeProvider theme={LightTheme}>
              <div>
                <ModuleBox>
                  <ModuleHeader>Account Verification</ModuleHeader>

                  <StepWizard
                    steps={finalSteps}
                    activeStep={stepStatus.activeStep}
                  />
                </ModuleBox>
              </div>
            </ThemeProvider>
          </PageWrapper>
        </WrapperDiv>
      );
    } else if (loadStatus.error) {
      return (
        <WrapperDiv>
          <PageWrapper style={{ display: "flex", flexDirection: "column" }}>
            <div>
              <ModuleBox>
                <ModuleHeader>Account Verification</ModuleHeader>

                <div style={{ margin: "1em" }}>
                  <p>
                    You can't send money until you finish verifying your
                    account.
                  </p>

                  <p>In order to verify your account we will need:</p>

                  <ul>
                    <li>Business Details</li>
                    <li>
                      Business Documents (e.g. Incorporation, Beneficial Owner
                      IDs)
                    </li>
                    <li>Bank Account Details</li>
                    <li>Bank Account Documents (e.g. Statement)</li>
                  </ul>

                  {userId === null || typeof userId === "undefined" ? null : (
                    <Row>
                      <InputObject>
                        <InputLabel>Bank Account</InputLabel>
                        <div style={{ display: "flex" }}>
                          <input
                            type="checkbox"
                            name="is_bank_account"
                            onChange={this.handleInputChange}
                            checked={this.state.is_bank_account}
                          />
                          <p style={{ margin: 0 }}>
                            {this.state.is_bank_account ? "Yes" : "No"}
                          </p>
                        </div>
                      </InputObject>
                    </Row>
                  )}

                  <AsyncButton
                    buttonText={<span>Get Started</span>}
                    onClick={this.props.nextStep}
                    label={"Get Started"}
                  />
                </div>
              </ModuleBox>
            </div>
          </PageWrapper>
        </WrapperDiv>
      );
    } else {
      return (
        <WrapperDiv>
          <p>Something went wrong</p>
        </WrapperDiv>
      );
    }
  }
}
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BusinessVerificationPage);

const InputObject = styled.label`
  display: block;
  padding: 1em;
  font-size: 15px;
`;

const InputLabel = styled.div`
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 5px;
`;
