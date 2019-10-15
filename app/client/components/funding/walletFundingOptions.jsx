import React from 'react';
import styled from 'styled-components';

import WyreBankFunding from "./wyreBankFunding.jsx"
import { EthAddress } from "./ethAddress.jsx"

export default class WalletFundingOptions extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      activeOption: 0,
    };
    this._isActive = this._isActive.bind(this);
  }

  _isActive(index) {
    this.setState({activeOption: index})
  }

  render() {
    let { activeOption } = this.state;
    let options = [
      {title: 'Bank Transfer', component: <WyreBankFunding />},
      {title: 'Blockchain Address', component: <EthAddress />}
    ];

    let activeOptionComponent = options[activeOption].component;

    return (
      <div>

        <WalletOptionWrapper>
        {options.map((option, index) => {
          return(
            <StyledOption color={(index === activeOption ? '#269094' : '#555')}  backgroundColor={(index === activeOption) ? '#f7fafc' : 'FFF'} key={index} onClick={() => this._isActive(index)}>
              {option.title}
            </StyledOption>
          )
        })}
        </WalletOptionWrapper>

        {activeOptionComponent}
      </div>
    )


  }
}

const WalletOptionWrapper = styled.div`
  display: flex;
  border: solid #dbe4e8;
  border-width: 0 0 1px;
`;

const StyledOption = styled.div`
  padding: 1em;
  font-weight: 400;
  background-color: ${props => props.backgroundColor};
  color: ${props => props.color};
`;