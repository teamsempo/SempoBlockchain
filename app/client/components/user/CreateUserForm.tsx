import * as React from "react";
import { connect } from "react-redux";

import { reduxForm, InjectedFormProps, formValueSelector } from "redux-form";
import QrReadingModal from "../qrReadingModal";
import { ErrorMessage, ModuleHeader } from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from "../form/InputField";
import SelectField from "../form/SelectField";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { TransferAccountTypes } from "../transferAccount/types";
import { Token } from "../../reducers/token/types";
import { getActiveToken } from "../../utils";

export interface ICreateUser {
  firstName?: string;
  lastName?: string;
  publicSerialNumber?: string;
  phone?: string;
  initialDisbursement?: number;
  bio?: string;
  gender?: string;
  referredBy?: string;
  location?: string;
  businessUsage?: string;
  usageOtherSpecific?: string;
  accountTypes: string[];
}

export interface ICreateVendor {
  firstName?: string;
  lastName?: string;
  publicSerialNumber?: string;
  phone?: string;
  isCashierAccount?: boolean;
  existingVendorPhone?: string;
  existingVendorPin?: string;
  location?: string;
  transferAccountName?: string;
}

export type ICreateUserUpdate = ICreateUser & ICreateVendor;

interface OuterProps {
  users: any;
  transferUsages: TransferUsage[];
}

interface StateProps {
  accountTypes: string[];
  businessUsageValue?: string;
  activeToken: Token;
  defaultDisbursement: any;
  validRoles: TransferAccountTypes[];
}

type Props = OuterProps & StateProps;

const validate = (values: ICreateUser) => {
  const errors: any = {};

  if (!values.phone && !values.publicSerialNumber) {
    errors.phone = "Must provide either phone number or ID number";
  }

  return errors;
};

class CreateUserForm extends React.Component<
  InjectedFormProps<ICreateUser, Props> & Props
> {
  componentDidMount() {
    const { defaultDisbursement, validRoles } = this.props;
    this.props.initialize({
      accountTypes: [validRoles[0]],
      gender: "female",
      initialDisbursement: defaultDisbursement
    });
  }

  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, "");
    this.props.change("publicSerialNumber", cleanedData);
  }

  optionizeUsages() {
    return this.props.transferUsages
      .map(transferUsage => {
        return {
          name: transferUsage.name,
          value: transferUsage.name
        };
      })
      .concat({
        name: "Other",
        value: "other"
      });
  }

  render() {
    const {
      activeToken,
      businessUsageValue,
      transferUsages,
      accountTypes,
      defaultDisbursement,
      validRoles
    } = this.props;
    let initialDisbursementAmount;
    let businessUsage;

    if (defaultDisbursement > 0) {
      initialDisbursementAmount = (
        <InputField
          name="initialDisbursement"
          label={"Initial Disbursement Amount"}
        >
          {activeToken !== null && typeof activeToken !== "undefined"
            ? activeToken.symbol
            : null}
        </InputField>
      );
    }
    if (transferUsages.length > 0) {
      if (businessUsageValue && businessUsageValue.toLowerCase() === "other") {
        businessUsage = (
          <>
            <SelectField
              name="businessUsage"
              label="Business Category"
              options={this.optionizeUsages()}
            />
            <InputField
              name="usageOtherSpecific"
              label="Please specify the category"
              isRequired
              isNotOther
            />
          </>
        );
      } else {
        businessUsage = (
          <SelectField
            name="businessUsage"
            label="Business Category"
            options={this.optionizeUsages()}
          />
        );
      }
    }

    let selectedUserForm = <></>;
    let selectedCashierForm = <></>;
    let selectedVendorForm = <></>;
    let selectedTokenAgentForm = <></>;
    const accountTypesList = accountTypes || [];
    if (accountTypesList.includes("beneficiary")) {
      selectedUserForm = <>{initialDisbursementAmount}</>;
    }
    if (accountTypesList.includes("cashier")) {
      selectedCashierForm = (
        <div>
          <div>
            To create a cashier account, enter the <strong>vendor's</strong>{" "}
            phone and pin.
          </div>
          <InputField
            name="existingVendorPhone"
            label={"Vendor Phone Number"}
          />
          <InputField
            name="existingVendorPin"
            type="password"
            label={"Vendor PIN"}
          />
        </div>
      );
    }
    if (
      accountTypesList.includes("vendor") ||
      accountTypesList.includes("cashier") ||
      accountTypesList.includes("supervendor")
    ) {
      selectedVendorForm = (
        <div>
          {businessUsage}
          <InputField name="transferAccountName" label={"Store Name"} />
        </div>
      );
    }
    if (accountTypesList.includes("token_agent")) {
      selectedTokenAgentForm = <></>;
    }

    return (
      <div>
        <ModuleHeader>Create an account</ModuleHeader>

        <div style={{ padding: "1em" }}>
          <form onSubmit={this.props.handleSubmit}>
            <InputField
              {...accountTypes}
              name="accountTypes"
              label={"Account Types"}
              isMultipleChoice={true}
              options={validRoles}
              style={{ minWidth: "200px" }}
            />
            <InputField name="publicSerialNumber" label={"ID Number"}>
              {/*
                // @ts-ignore */}
              <QrReadingModal
                updateData={(data: string) => this.setSerialNumber(data)}
              />
            </InputField>{" "}
            <span>or</span>
            <InputField name="phone" label={"Phone Number"} isPhoneNumber />
            <InputField name="firstName" label="Given Name(s)" isRequired />
            <InputField name="lastName" label="Family/Surname" />
            {/*<InputField name="bio" label="Directory Entry" />*/}
            <InputField name="location" label="Location" />
            <SelectField
              name="gender"
              label="Gender"
              options={["Female", "Male", "Other"]}
              hideNoneOption={true}
            />
            {selectedUserForm}
            {selectedCashierForm}
            {selectedVendorForm}
            {selectedTokenAgentForm}
            <ErrorMessage>{this.props.users.createStatus.error}</ErrorMessage>
            <AsyncButton
              type="submit"
              isLoading={this.props.users.createStatus.isRequesting}
              buttonStyle={{ display: "flex" }}
              buttonText={<span>Submit</span>}
            />
          </form>
        </div>
      </div>
    );
  }
}

const CreateUserFormReduxForm = reduxForm<ICreateUser, Props>({
  form: "createUser",
  validate
})(CreateUserForm);

export default connect(
  (state: any): StateProps => {
    const selector = formValueSelector("createUser");
    return {
      accountTypes: selector(state, "accountTypes"),
      businessUsageValue: selector(state, "businessUsage"),
      activeToken: getActiveToken(state),
      defaultDisbursement:
        state.organisations.byId[state.login.organisationId]
          .default_disbursement / 100,
      validRoles:
        state.organisations.byId[state.login.organisationId].valid_roles || []
    };
  }
)(CreateUserFormReduxForm);
