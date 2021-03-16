import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";
import { Input } from "../styledElements";

import { WyreAction } from "../../reducers/wyre/actions";
import LoadingSpinner from "../loadingSpinner.jsx";
import AsyncButton from "../AsyncButton.jsx";
import { BusinessVerificationAction } from "../../reducers/businessVerification/actions";

const mapStateToProps = state => {
  return {
    businessVerificationStatus: state.businessVerification.loadStatus,
    bankAccounts:
      state.businessVerification.businessVerificationState.bank_accounts,
    wyreTransferStatus: state.wyre.createWyreTransferStatus,
    wyreTransfer: state.wyre.wyreState.wyre_transfer
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadBusinessProfile: () =>
      dispatch(BusinessVerificationAction.loadBusinessVerificationRequest()),
    createWyreTransfer: body =>
      dispatch(WyreAction.createWyreTransferRequest({ body }))
  };
};

var timeout = null;

class WyreBankFunding extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      starting_total: "",
      result_total: "10",
      isLive: false
    };
    this.handleKeypress = this.handleKeypress.bind(this);
    this.handleKeyUp = this.handleKeyUp.bind(this);
    this.fundAccount = this.fundAccount.bind(this);
  }

  componentDidMount() {
    this.props.loadBusinessProfile();
  }

  componentDidUpdate(newProps) {
    let { wyreTransfer, bankAccounts } = this.props;

    if (newProps.bankAccounts !== bankAccounts) {
      this.fundAccount(false);
    }

    if (newProps.wyreTransfer !== wyreTransfer) {
      if (wyreTransfer !== null && typeof wyreTransfer !== "undefined") {
        this.setState({
          starting_total: wyreTransfer.sourceAmount,
          result_total: wyreTransfer.destAmount
        });
      }
    }
  }

  handleKeyUp(e) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      this.fundAccount(false);
    }, 500);
  }

  handleKeypress(e) {
    const target = e.target;
    const value = target.value;
    const name = target.name;

    const characterCode = e.key;
    if (characterCode === "Backspace") {
      return;
    }

    if (characterCode === "-" || characterCode === "e") {
      e.preventDefault();
      return;
    }

    if (name === "result_total") {
      this.setState({
        [name]: value,
        starting_total: ""
      });
    } else if (name === "starting_total") {
      this.setState({
        [name]: value,
        result_total: ""
      });
    }
  }

  fundAccount(isReal) {
    let { bankAccounts } = this.props;

    if (bankAccounts !== null && typeof bankAccounts !== "undefined") {
      var bankCurrency = bankAccounts[0].currency.toUpperCase();
      this.props.createWyreTransfer({
        source_currency: bankCurrency,
        source_amount: this.state.starting_total,
        dest_amount: this.state.result_total,
        preview: !isReal,
        include_fees: true
      });
    }
  }

  render() {
    let {
      businessVerificationStatus,
      bankAccounts,
      wyreTransfer,
      wyreTransferStatus
    } = this.props;
    var bankCurrency = null;
    var conversionFee = null;
    var exchangeRate = null;
    var sourceName = null;
    var bankNumber = null;

    var isLoading = wyreTransferStatus.isRequesting && this.state.isLive;

    if (bankAccounts !== null && typeof bankAccounts !== "undefined") {
      bankCurrency = bankAccounts[0].currency.toUpperCase();
    }

    if (wyreTransfer !== null && typeof wyreTransfer !== "undefined") {
      conversionFee = wyreTransfer.fees[bankCurrency];
      exchangeRate = wyreTransfer.exchangeRate;
      sourceName = wyreTransfer.sourceName.slice(0, -4);
      bankNumber = wyreTransfer.sourceName.slice(-4);
    }

    if (businessVerificationStatus.isRequesting) {
      return (
        <div style={{ margin: "1em" }}>
          <LoadingSpinner />
        </div>
      );
    } else if (businessVerificationStatus.success) {
      return (
        <div>
          <StyledExchangeWrapper>
            <div>
              <InputLabel>Send {bankCurrency}</InputLabel>
              <ManagerInput
                min="1"
                name="starting_total"
                placeholder={"0.00"}
                type="number"
                value={this.state.starting_total}
                onKeyDown={this.handleKeypress}
                onKeyUp={this.handleKeyUp}
                onChange={this.handleKeypress}
              />
            </div>

            <p>FOR</p>

            <div>
              <InputLabel>Receive DAI</InputLabel>
              <ManagerInput
                min="1"
                name="result_total"
                placeholder={"0.00"}
                type="number"
                value={this.state.result_total}
                onChange={this.handleKeypress}
                onKeyUp={this.handleKeyUp}
                onKeyDown={this.handleKeypress}
              />
            </div>
          </StyledExchangeWrapper>

          <PreviewWrapper>
            <div>
              <FundingText>
                Convert and receive {this.state.result_total}
              </FundingText>
              <div>
                <SmallText>
                  Exchange Rate: <Bold>{exchangeRate}</Bold>
                </SmallText>
                <SmallText>
                  Conversion Fee: <Bold>{conversionFee}</Bold>
                </SmallText>
                <SmallText>
                  {sourceName} <Bold>{bankNumber}</Bold>
                </SmallText>
              </div>
            </div>

            <ButtonWrapper>
              <AsyncButton
                buttonStyle={{ display: "flex" }}
                onClick={() =>
                  this.setState({ isLive: true }, () => this.fundAccount(true))
                }
                buttonText={<span>FUND ACCOUNT</span>}
                isLoading={isLoading}
                label={"Fund Account"}
              />
            </ButtonWrapper>
          </PreviewWrapper>
        </div>
      );
    } else {
      return (
        <div>
          <p>Something went wrong.</p>
        </div>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(WyreBankFunding);

const Bold = styled.span`
  font-weight: 600;
`;

const SmallText = styled.p`
  color: #384053;
  font-size: 12px;
`;

const FundingText = styled.p`
  font-size: 20px;
  font-weight: 500;
`;

const ButtonWrapper = styled.div`
  align-items: center;
  display: flex;
`;

const PreviewWrapper = styled.div`
  flex-wrap: wrap;
  background-color: #f7fafc;
  display: flex;
  margin: 1em;
  padding: 1em;
  justify-content: space-between;
`;

const StyledExchangeWrapper = styled.div`
  display: flex;
  justify-content: space-between;
  margin: 1em;
  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const ManagerInput = styled(Input)`
  margin: 0;
  width: fit-content;
`;

const InputLabel = styled.div`
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 5px;
`;
