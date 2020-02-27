import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import { loadWyreAccountBalance } from "../../reducers/wyreReducer";
import LoadingSpinner from "../loadingSpinner.jsx";

const mapStateToProps = state => {
  return {
    wyreAccountStatus: state.wyre.loadWyreAccountStatus,
    wyreAccount: state.wyre.wyreState.wyre_account
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadWyreAccount: () => dispatch(loadWyreAccountBalance())
  };
};

class WyreWalletBalance extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    // todo-- fix this
    // this.props.loadWyreAccount()
  }

  render() {
    let { wyreAccountStatus, wyreAccount } = this.props;

    if (wyreAccount !== null && typeof wyreAccount !== undefined) {
      var balance = "$" + wyreAccount.availableBalances["USD"] + " USD";
    } else {
      balance = "You currently have no balance";
    }

    if (wyreAccountStatus.isRequesting) {
      return (
        <div style={{ margin: "1em" }}>
          <LoadingSpinner />
        </div>
      );
    } else if (wyreAccountStatus.success) {
      return (
        <WalletWrapper>
          <StyledHeader>Your balance</StyledHeader>
          <StyledBalance>{balance}</StyledBalance>
        </WalletWrapper>
      );
    } else if (wyreAccountStatus.error !== null) {
      return (
        <WalletWrapper>
          <StyledHeader>Your balance</StyledHeader>
          <StyledBalance>$0.00</StyledBalance>
        </WalletWrapper>
      );
    } else {
      return (
        <WalletWrapper>
          <StyledHeader>Your balance</StyledHeader>
          <StyledBalance>$0.00</StyledBalance>
        </WalletWrapper>
      );
    }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(WyreWalletBalance);

const WalletWrapper = styled.div`
  display: flex;
  margin: 1em;
  flex-direction: column;
`;

const StyledHeader = styled.p`
  font-size: 12px;
  font-weight: 600;
  margin: 0 0 0.6em;
`;

const StyledBalance = styled.p`
  font-size: 20px;
  margin: 0;
`;
