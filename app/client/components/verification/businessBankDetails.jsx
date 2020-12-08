import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import { ModuleHeader, Row, StyledSelect, Input } from "../styledElements";

import { DefaultTheme } from "../theme";
import AsyncButton from "../AsyncButton.jsx";

import { BusinessVerificationAction } from "../../reducers/businessVerification/actions";

const ErrorMessage = function(props) {
  var error = props.input + "_val";
  var error_message = props.input + "_val_msg";

  return (
    <div
      style={{ display: props.state[error] ? "none" : "flex", color: "red" }}
    >
      {props.state[error_message]}
    </div>
  );
};

const mapStateToProps = state => {
  return {
    createBankAccountStatus: state.businessVerification.createBankAccountStatus,
    editBankAccountStatus: state.businessVerification.editBankAccountStatus,
    businessProfile: state.businessVerification.businessVerificationState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    createBankAccount: body =>
      dispatch(BusinessVerificationAction.createBankAccountRequest({ body })),
    editBankAccount: (body, path) =>
      dispatch(
        BusinessVerificationAction.editBankAccountRequest({ body, path })
      ),
    backStep: () => dispatch(BusinessVerificationAction.updateActiveStep(2))
  };
};

class BusinessBankDetails extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      routing_number: "",
      account_number: "",
      currency: "select"
    };
    this.handleInputChange = this.handleInputChange.bind(this);
    this.isValidated = this.isValidated.bind(this);
  }

  componentDidMount() {
    let { businessProfile } = this.props;

    // only support ONE bank account currently.
    let bank_account = businessProfile.bank_accounts[0];

    // set initial form state
    if (bank_account !== null && typeof bank_account !== "undefined") {
      Object.keys(this.state).map(key => {
        if (
          bank_account[key] !== null &&
          typeof bank_account[key] !== "undefined"
        ) {
          this.setState({ [key]: bank_account[key] });
        }
      });
    }
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.type === "checkbox" ? target.checked : target.value;
    const name = target.name;

    this.setState({
      [name]: value,
      error_message: ""
    });
  }

  isValidated() {
    const userInput = this._grabUserInput(); // grab user entered vals
    const validateNewInput = this._validateData(userInput); // run the new input against the validator

    if (
      Object.keys(validateNewInput).every(k => {
        return validateNewInput[k] === true;
      })
    ) {
      // only support ONE bank account currently.
      let bank_account = this.props.businessProfile.bank_accounts[0];

      if (bank_account !== null && typeof bank_account !== "undefined") {
        if (Object.keys(bank_account).length === 1) {
          // only country is saved in redux. create a new bank account in db.
          this.props.createBankAccount(userInput);
        } else {
          // bank account exists in db
          this.props.editBankAccount(userInput, bank_account.id);
        }
      }
    } else {
      // if anything fails then update the UI validation state but NOT the UI Data State
      this.setState(
        Object.assign(
          userInput,
          validateNewInput,
          this._validationErrors(validateNewInput)
        )
      );
    }
  }

  _grabUserInput() {
    let { routing_number, account_number, currency } = this.state;
    let { businessProfile } = this.props;
    return {
      routing_number: routing_number,
      account_number: account_number,
      currency: currency,
      bank_country: businessProfile.bank_accounts[0].bank_country,
      kyc_application_id: businessProfile.id
    };
  }

  _validateData(data) {
    return {
      routing_number_val: /^[0-9]*\S.*$/.test(data.routing_number), // numbers only and not empty
      account_number_val: /^[0-9]*\S.*$/.test(data.account_number), // numbers only and not empty
      currency_val: data.currency !== "select" // not default
    };
  }

  _validationErrors(val) {
    const errMsgs = {
      routing_number_val_msg: val.routing_number
        ? ""
        : "Please provide a valid routing number",
      account_number_val_msg: val.account_number
        ? ""
        : "Please provide a valid account_number",
      currency_val_msg: val.currency ? "" : "Please select a currency"
    };
    return errMsgs;
  }

  render() {
    let { businessProfile } = this.props;
    let currencyOptions = ["aud", "eur", "gbp", "usd"];

    return (
      <div>
        <Row>
          <InputObject>
            <InputLabel>
              {businessProfile.bank_accounts[0].bank_country === "Australia"
                ? "BSB"
                : "Routing Number"}
            </InputLabel>
            <ManagerInput
              name="routing_number"
              placeholder={
                businessProfile.bank_accounts[0].bank_country === "Australia"
                  ? "123123"
                  : "123123123"
              }
              type="text"
              value={this.state.routing_number}
              onChange={this.handleInputChange}
            />
            <ErrorMessage state={this.state} input={"routing_number"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>Account Number</InputLabel>
            <ManagerInput
              name="account_number"
              placeholder="12341234"
              type="text"
              value={this.state.account_number}
              onChange={this.handleInputChange}
            />
            <ErrorMessage state={this.state} input={"account_number"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>Currency</InputLabel>
            <StyledSelectKey
              name="currency"
              value={this.state.currency}
              onChange={this.handleInputChange}
            >
              <option name="select" value="select" disabled>
                Select
              </option>
              {currencyOptions.map((currency, index) => {
                return (
                  <option key={index} name={currency} value={currency}>
                    {currency}
                  </option>
                );
              })}
            </StyledSelectKey>
            <ErrorMessage state={this.state} input={"currency"} />
          </InputObject>
        </Row>

        <ThemeProvider theme={DefaultTheme}>
          <div style={{ display: "flex" }}>
            <AsyncButton
              buttonText={<span>Back</span>}
              onClick={this.props.backStep}
              label={"Back"}
            />
            <AsyncButton
              buttonText={<span>Next</span>}
              label={"Next"}
              onClick={this.isValidated}
              isLoading={
                this.props.editBankAccountStatus.isRequesting ||
                this.props.createBankAccountStatus.isRequesting
              }
              buttonStyle={{ display: "flex" }}
            />
          </div>
        </ThemeProvider>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BusinessBankDetails);

const ManagerInput = styled(Input)`
  margin: 0;
`;

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

const StyledSelectKey = styled(StyledSelect)`
  box-shadow: 0 0 0 1px rgba(44, 45, 48, 0.15);
  font: 400 12px system-ui;
  color: #777;
  padding: 0 0 0 10px;
  margin: 5px;
  line-height: 25px;
  height: 25px;
`;
