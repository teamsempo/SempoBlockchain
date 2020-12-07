import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import { Row, Input, StyledSelect } from "../styledElements";

import { CountryDropdown, RegionDropdown } from "react-country-region-selector";
import { BusinessVerificationAction } from "../../reducers/businessVerification/actions";
import AsyncButton from "../AsyncButton.jsx";
import { DefaultTheme } from "../theme.js";

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

const mapStateToProps = (state, ownProps) => {
  return {
    userId: ownProps.userId,
    editStatus: state.businessVerification.editStatus,
    businessProfile: state.businessVerification.businessVerificationState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    editBusinessProfile: (body, path) =>
      dispatch(
        BusinessVerificationAction.editBusinessVerificationRequest({
          body,
          path
        })
      ),
    createBusinessProfile: body =>
      dispatch(
        BusinessVerificationAction.createBusinessVerificationRequest({ body })
      ),
    nextStep: () => dispatch(BusinessVerificationAction.updateActiveStep(1))
  };
};

class BusinessDetails extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      account_type: "BUSINESS",
      first_name: "",
      last_name: "",
      phone: "",
      business_legal_name: "",
      business_type: "select",
      tax_id: "",
      website: "",
      date_established: "",
      country: "",
      street_address: "",
      street_address_2: "",
      city: "",
      region: "",
      postal_code: "",
      beneficial_owners: [{ full_name: "" }]
    };
    this._validateOnDemand = false; // this flag enables onBlur validation as user fills forms

    this.handleInputChange = this.handleInputChange.bind(this);
    this.selectCountry = this.selectCountry.bind(this);
    this.selectRegion = this.selectRegion.bind(this);
    this.handleBeneficialOwner = this.handleBeneficialOwner.bind(this);
    this.addOwner = this.addOwner.bind(this);
    this.validationCheck = this.validationCheck.bind(this);
    this.isValidated = this.isValidated.bind(this);
  }

  componentDidMount() {
    let { businessProfile } = this.props;

    // set initial form state
    if (businessProfile !== null && typeof businessProfile !== "undefined") {
      Object.keys(this.state).map(key => {
        if (
          businessProfile[key] !== null &&
          typeof businessProfile[key] !== "undefined"
        ) {
          this.setState({ [key]: businessProfile[key] });
        }
      });
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

  selectCountry(val) {
    this.setState({ country: val });
  }

  selectRegion(val) {
    this.setState({ region: val });
  }

  addOwner = e => {
    this.setState(prevState => ({
      beneficial_owners: [...prevState.beneficial_owners, { full_name: "" }]
    }));
  };

  handleBeneficialOwner(e) {
    let beneficial_owners = [...this.state.beneficial_owners];
    beneficial_owners[e.target.dataset.id].full_name = e.target.value;
    this.setState({ beneficial_owners: beneficial_owners });
  }

  isValidated() {
    const userInput = this._grabUserInput(); // grab user entered vals
    const validateNewInput = this._validateData(userInput); // run the new input against the validator
    const createBusinessProfile = {
      ...userInput,
      ...{ user_id: this.props.userId }
    };

    if (
      Object.keys(validateNewInput).every(k => {
        return validateNewInput[k] === true;
      })
    ) {
      // get business verification profile
      let business = Object.keys(this.props.businessProfile);

      if (business.length > 0) {
        // business profile exists in db
        this.props.nextStep();
        this.props.editBusinessProfile(
          userInput,
          this.props.businessProfile.id
        );
      } else {
        // creating a new business profile in db
        this.props.nextStep();
        this.props.createBusinessProfile(createBusinessProfile);
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
    let {
      account_type,
      phone,
      business_legal_name,
      business_type,
      tax_id,
      website,
      date_established,
      country,
      street_address,
      street_address_2,
      city,
      region,
      postal_code,
      beneficial_owners
    } = this.state;
    return {
      account_type: account_type,
      phone: phone,
      business_legal_name: business_legal_name,
      business_type: business_type,
      tax_id: tax_id,
      website: website,
      date_established: date_established,
      country: country,
      street_address: street_address,
      street_address_2: street_address_2,
      city: city,
      region: region,
      postal_code: postal_code,
      beneficial_owners: beneficial_owners
    };
  }

  validationCheck() {
    if (!this._validateOnDemand) {
      return;
    }

    const userInput = this._grabUserInput(); // grab user entered vals
    const validateNewInput = this._validateData(this.state); // run the new input against the validator
    console.log(validateNewInput);

    this.setState(
      Object.assign(
        userInput,
        validateNewInput,
        this._validationErrors(validateNewInput)
      )
    );
  }

  _validateData(data) {
    let businessValidation;
    if (this.state.account_type === "BUSINESS") {
      businessValidation = {
        phone_val: /^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$/.test(
          data.phone
        ), // phone
        business_legal_name_val: /.*\S.*/.test(data.business_legal_name), // is not empty
        business_type_val: data.business_type !== "select", // not default
        tax_id_val: /.*\S.*/.test(data.tax_id), // not empty
        website_val: /(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]/g.test(
          data.website
        ), // domain name
        date_established_val: /^([0-2][0-9]|(3)[0-1])(\/)(((0)[0-9])|((1)[0-2]))(\/)\d{4}$/i.test(
          data.date_established
        ), // dd/mm/yyyy
        beneficial_owners_val:
          data.beneficial_owners.filter(owner => owner.full_name !== "")
            .length > 0
      };
    }

    return {
      ...businessValidation,
      // account_type_val: no validation
      country_val: /.*\S.*/.test(data.country), // not empty
      street_address_val: /.*\S.*/.test(data.street_address), // not empty
      // street_address_2: no validation
      city_val: /.*\S.*/.test(data.city), // not empty
      region_val: /.*\S.*/.test(data.region), // not empty
      postal_code_val: /^[0-9]*\S.*$/.test(data.postal_code) // numbers only and not empty
    };
  }

  _validationErrors(val) {
    const errMsgs = {
      // account_type_val_msg: val.account_type ? '' : 'Account type must be selected',
      phone_val_msg: val.phone ? "" : "Please provide a valid phone number",
      business_legal_name_val_msg: val.business_legal_name
        ? ""
        : "Please provide a business name",
      business_type_val_msg: val.business_type
        ? ""
        : "Please select a business type",
      tax_id_val_msg: val.tax_id ? "" : "Please provide your tax ID",
      website_val_msg: val.website ? "" : "Please provide a valid website",
      date_established_val_msg: val.date_established
        ? ""
        : "Please provide establishment date as dd/mm/yyyy",
      country_val_msg: val.country ? "" : "Please select a country",
      street_address_val_msg: val.street_address
        ? ""
        : "Please provide your street address",
      city_val_msg: val.city ? "" : "Please provide a city",
      region_val_msg: val.region ? "" : "Please select a region",
      postal_code_val_msg: val.postal_code
        ? ""
        : "Please provide a postal code",
      beneficial_owners_val_msg: val.beneficial_owners
        ? ""
        : "Please add at least one beneficial owner"
    };
    return errMsgs;
  }

  render() {
    const { userId } = this.props;
    let indvidualAccount = this.state.account_type === "INDIVIDUAL";

    return (
      <div>
        {userId === null || typeof userId === "undefined" ? null : (
          <Row>
            <InputObject>
              <InputLabel>Account Type</InputLabel>
              <StyledSelectKey
                name="account_type"
                value={this.state.account_type}
                onBlur={this.validationCheck}
                onChange={this.handleInputChange}
              >
                <option name="INDIVIDUAL" value="INDIVIDUAL">
                  INDIVIDUAL
                </option>
                <option name="BUSINESS" value="BUSINESS">
                  BUSINESS
                </option>
              </StyledSelectKey>
              <ErrorMessage state={this.state} input={"account_type"} />
            </InputObject>
          </Row>
        )}

        {indvidualAccount ? null : (
          <div>
            <Row>
              <InputObject>
                <InputLabel>Phone</InputLabel>
                <ManagerInput
                  name="phone"
                  placeholder="+61411003945"
                  type="text"
                  value={this.state.phone}
                  onBlur={this.validationCheck}
                  onChange={this.handleInputChange}
                />
                <ErrorMessage state={this.state} input={"phone"} />
              </InputObject>
            </Row>

            <Row>
              <InputObject>
                <InputLabel>Business Legal Name</InputLabel>
                <ManagerInput
                  name="business_legal_name"
                  placeholder="Acme Aus"
                  type="text"
                  value={this.state.business_legal_name}
                  onBlur={this.validationCheck}
                  onChange={this.handleInputChange}
                />
                <ErrorMessage
                  state={this.state}
                  input={"business_legal_name"}
                />
              </InputObject>
            </Row>

            <Row>
              <InputObject>
                <InputLabel>Business Type</InputLabel>
                <StyledSelectKey
                  name="business_type"
                  value={this.state.business_type}
                  onBlur={this.validationCheck}
                  onChange={this.handleInputChange}
                >
                  <option name="select" value="select" disabled>
                    select attribute
                  </option>
                  <option name="partnership" value="partnership">
                    General Partnership
                  </option>
                  <option name="for_profit" value="for_profit">
                    For-Profit Corporation
                  </option>
                  <option name="limited_company" value="limited_company">
                    Limited Company
                  </option>
                  <option name="llc" value="llc">
                    Limited Liability Company (LLC)
                  </option>
                  <option name="llp" value="llp">
                    Limited Liability Partnership (LLP)
                  </option>
                  <option name="lp" value="lp">
                    Limited Partnership (LP)
                  </option>
                  <option name="non_profit" value="non_profit">
                    Non-for Profit
                  </option>
                  <option name="other" value="other">
                    Other
                  </option>
                </StyledSelectKey>
                <ErrorMessage state={this.state} input={"business_type"} />
              </InputObject>
            </Row>

            <Row>
              <InputObject>
                <InputLabel>Tax Identification Number</InputLabel>
                <ManagerInput
                  name="tax_id"
                  placeholder="Tax ID"
                  type="text"
                  value={this.state.tax_id}
                  onBlur={this.validationCheck}
                  onChange={this.handleInputChange}
                />
                <ErrorMessage state={this.state} input={"tax_id"} />
              </InputObject>
            </Row>

            <Row>
              <InputObject>
                <InputLabel>Website</InputLabel>
                <ManagerInput
                  name="website"
                  placeholder="https://acmecorp.com"
                  type="text"
                  value={this.state.website}
                  onBlur={this.validationCheck}
                  onChange={this.handleInputChange}
                />
                <ErrorMessage state={this.state} input={"website"} />
              </InputObject>
            </Row>

            <Row>
              <InputObject>
                <InputLabel>Date Business Established</InputLabel>
                <ManagerInput
                  name="date_established"
                  placeholder="dd/mm/yyyy"
                  type="text"
                  value={this.state.date_established}
                  onBlur={this.validationCheck}
                  onChange={this.handleInputChange}
                />
                <ErrorMessage state={this.state} input={"date_established"} />
              </InputObject>
            </Row>
          </div>
        )}

        <Row>
          <InputObject>
            <InputLabel>Country</InputLabel>
            <StyledCountryPicker
              name="country"
              defaultOptionLabel="Select a country"
              value={this.state.country}
              onBlur={this.validationCheck}
              onChange={val => this.selectCountry(val)}
            />
            <ErrorMessage state={this.state} input={"country"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>Street Address</InputLabel>
            <ManagerInput
              name="street_address"
              placeholder="255 W 36th Street"
              type="text"
              value={this.state.street_address}
              onBlur={this.validationCheck}
              onChange={this.handleInputChange}
            />
            <ErrorMessage state={this.state} input={"street_address"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>Address 2</InputLabel>
            <ManagerInput
              name="street_address_2"
              placeholder="305"
              type="text"
              value={this.state.street_address_2}
              onBlur={this.validationCheck}
              onChange={this.handleInputChange}
            />
            <ErrorMessage state={this.state} input={"street_address_2"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>City</InputLabel>
            <ManagerInput
              name="city"
              placeholder="New York City"
              type="text"
              value={this.state.city}
              onBlur={this.validationCheck}
              onChange={this.handleInputChange}
            />
            <ErrorMessage state={this.state} input={"city"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>Region</InputLabel>
            <StyledRegionDropdown
              blankOptionLabel="No country selected"
              defaultOptionLabel="Select a region"
              country={this.state.country}
              value={this.state.region}
              onBlur={this.validationCheck}
              onChange={this.selectRegion}
            />
            <ErrorMessage state={this.state} input={"region"} />
          </InputObject>
        </Row>

        <Row>
          <InputObject>
            <InputLabel>Postal Code</InputLabel>
            <ManagerInput
              name="postal_code"
              placeholder="100018"
              type="text"
              value={this.state.postal_code}
              onBlur={this.validationCheck}
              onChange={this.handleInputChange}
            />
            <ErrorMessage state={this.state} input={"postal_code"} />
          </InputObject>
        </Row>

        {indvidualAccount ? null : (
          <Row>
            <InputObject>
              <InputLabel>
                Beneficial Owners (Directly or indirectly owns more than 25% of
                the Applicant or has effective control over the Applicant)
              </InputLabel>
              {this.state.beneficial_owners.map((owner, index) => {
                let ownerId = `owner-${index}`;
                return (
                  <div key={index}>
                    <ManagerInput
                      style={{ margin: "0.5em 0" }}
                      name={ownerId}
                      data-id={index}
                      placeholder="John Smith"
                      type="text"
                      value={this.state.beneficial_owners[index].full_name}
                      onChange={this.handleBeneficialOwner}
                    />
                  </div>
                );
              })}
              <ErrorMessage state={this.state} input={"beneficial_owners"} />
              <TheRealInputButton onClick={this.addOwner}>
                Add new owner
              </TheRealInputButton>
            </InputObject>
          </Row>
        )}

        <ThemeProvider theme={DefaultTheme}>
          <AsyncButton
            buttonText={<span>Next</span>}
            onClick={this.isValidated}
            isLoading={this.props.editStatus.isRequesting}
            buttonStyle={{ display: "flex" }}
            label={"Next"}
          />
        </ThemeProvider>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BusinessDetails);

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

// overwriting CountryDropdown component - copied from StyledSelect
const StyledCountryPicker = styled(CountryDropdown)`
  box-shadow: 0 0 0 1px rgba(44, 45, 48, 0.15);
  font: 400 12px system-ui !important;
  color: #777;
  padding: 0 0 0 10px;
  margin: 5px;
  line-height: 25px;
  height: 25px;
  outline: none;
  border: 0;
  white-space: nowrap;
  display: inline-block;
  background: ${props => props.theme.background};
  font-size: 1em;
  font-weight: 200;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  text-decoration: none;
  -webkit-transition: all 0.15s ease;
  transition: all 0.15s ease;
  &:hover {
    //background-color: #34b0b3;
    background-color: ${props => props.theme.backgroundColor};
  }
`;

const StyledRegionDropdown = styled(RegionDropdown)`
  box-shadow: 0 0 0 1px rgba(44, 45, 48, 0.15);
  font: 400 12px system-ui !important;
  color: #777;
  padding: 0 0 0 10px;
  margin: 5px;
  line-height: 25px;
  height: 25px;
  outline: none;
  border: 0;
  white-space: nowrap;
  display: inline-block;
  background: ${props => props.theme.background};
  font-size: 1em;
  font-weight: 200;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  text-decoration: none;
  -webkit-transition: all 0.15s ease;
  transition: all 0.15s ease;
  &:hover {
    //background-color: #34b0b3;
    background-color: ${props => props.theme.backgroundColor};
  }
`;

const TheRealInputButton = styled.label`
  background-color: #30a4a6;
  color: #fff;
  margin: 0.5em 0;
  line-height: 25px;
  height: 25px;
  position: relative;
  align-items: center;
  justify-content: center;
  outline: none;
  border: 0;
  white-space: nowrap;
  display: inline-block;
  padding: 0 14px;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  font-size: 1em;
  font-weight: 400;
  text-transform: uppercase;
  -webkit-letter-spacing: 0.025em;
  -moz-letter-spacing: 0.025em;
  -ms-letter-spacing: 0.025em;
  letter-spacing: 0.025em;
  text-decoration: none;
  -webkit-transition: all 0.15s ease;
  transition: all 0.15s ease;
  &:hover {
    background-color: #34b0b3;
  }
`;
