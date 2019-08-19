import React from 'react'
import styled from "styled-components";

export default class BusinessVerificationPending extends React.Component {
  render() {
    return(
      <div>
        <h3>Pending Verification</h3>
        <SecondaryText>We will verify your profile within the next 5 business days. We might get in contact to request further supporting information. For questions, please contact team@sempo.ai</SecondaryText>
      </div>
    )
  }
}

const SecondaryText = styled.p`
  color: #555555;
  font-size: 12px;
  padding-top: 0;
  margin: 0;
  font-weight: 600;
`;
