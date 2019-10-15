import React from 'react'
import styled from 'styled-components';

export const EthAddress = () => {
  return(
    <div>
      <StyledEthAddress>
        {window.USING_EXTERNAL_ERC20 ? window.MASTER_WALLET_ADDRESS : window.ETH_CONTRACT_ADDRESS}
      </StyledEthAddress>
      <div style={{margin: '1em'}}>
        <SecondaryText>
          To fund your Sempo account:
        </SecondaryText>
        <SecondaryDiv>
          <ul>
            <li>Send DAI to the above Ethereum address</li>
            <li>Funds will be available for distribution within 24 hours</li>
          </ul>
        </SecondaryDiv>
      </div>
    </div>
  )
};

const SecondaryDiv = styled.div`
  color: #555555;
  font-size: 12px;
  padding-top: 0;
  margin: 0;
  font-weight: 600;
`;

const SecondaryText = styled.p`
  color: #555555;
  font-size: 12px;
  padding-top: 0;
  margin: 0;
  font-weight: 600;
`;

const StyledEthAddress = styled.div`
  overflow: auto;
  margin: 1em;
  padding: 1em;
  border: 1px solid #dbe4e8;
  font-weight: 400;
  background-color: #f7fafc;
`;