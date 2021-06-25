import React, { useEffect } from "react";
import styled from "styled-components";
import { useSelector, useDispatch } from "react-redux";
import { BusinessVerificationAction } from "../reducers/businessVerification/actions";

import LoadingSpinner from "./loadingSpinner.jsx";
import { Link } from "react-router-dom";
import { ReduxState } from "../reducers/rootReducer";

interface Props {
  userId: number;
}

export default function GetVerified(props: Props) {
  const adminTier = useSelector((state: ReduxState) => state.login.adminTier);
  const loadStatus = useSelector(
    (state: ReduxState) => state.businessVerification.loadStatus
  );
  const businessProfile = useSelector(
    (state: ReduxState) => state.businessVerification.businessVerificationState
  );
  const dispatch = useDispatch();
  const { userId } = props;

  useEffect(() => {
    dispatch(BusinessVerificationAction.resetActiveStep());
    dispatch(BusinessVerificationAction.resetBusinessVerificationState());
    let query;
    if (userId) {
      query = { user_id: userId };
    }
    dispatch(
      BusinessVerificationAction.loadBusinessVerificationRequest({ query })
    );
  }, []);

  var iconColor = "#ff1705";
  var text: React.ReactFragment = "Please contact support.";
  var addFunds = null;

  if (loadStatus.isRequesting) {
    return (
      <WrapperDiv>
        <LoadingSpinner />
      </WrapperDiv>
    );
  }

  if (
    businessProfile.kyc_status === "INCOMPLETE" ||
    !(Object.values(businessProfile).length > 0)
  ) {
    if (adminTier === "superadmin") {
      text = <Link to="/settings/verification">Get Verified</Link>;
    }

    if (userId) {
      text = <Link to={`/users/${userId}/verification`}>Add User KYC</Link>;
    }
  }

  if (businessProfile.kyc_status === "PENDING") {
    iconColor = "#FF9800";
    text = "Pending.";
    addFunds = null;
  }

  if (businessProfile.kyc_status === "VERIFIED") {
    iconColor = "#00C759";
    text = "Verified.";
    addFunds = null;

    if ((!userId && adminTier === "superadmin") || adminTier === "admin") {
      addFunds = (
        <div>
          <br />
          <Link to="settings/fund-wallet">Add Funds</Link>
        </div>
      );
    }
  }

  return (
    <div style={{ margin: "1em" }}>
      <StyledAccountWrapper>
        <StyledHeader>Account Status:</StyledHeader>
        <StyledContent backgroundColor={iconColor}>{text}</StyledContent>
        {addFunds}
      </StyledAccountWrapper>
    </div>
  );
}

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const StyledHeader = styled.p`
  font-weight: 600;
  margin: 0 0 0.6em;
`;

interface ParaProps {
  backgroundColor: string;
}

const StyledContent = styled.p<ParaProps>`
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
