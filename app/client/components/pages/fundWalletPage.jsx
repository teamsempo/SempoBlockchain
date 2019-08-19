import React from 'react';
import styled, {ThemeProvider} from 'styled-components';

import {PageWrapper, ModuleHeader, ModuleBox } from '../styledElements';

import WalletFundingOptions from '../funding/walletFundingOptions.jsx';
import WyreWalletBalance from '../funding/wyreWalletBalance.jsx';

export default class FundWalletPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {

    return (
        <WrapperDiv>
          <PageWrapper style={{display: 'flex', flexDirection: 'column'}}>
            <div>

              <WyreWalletBalance />

              <ModuleBox>
                <WalletFundingOptions />
              </ModuleBox>

            </div>
          </PageWrapper>
        </WrapperDiv>
      );
  }
}

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;