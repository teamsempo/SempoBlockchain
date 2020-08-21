import * as React from "react";
import { connect } from "react-redux";

import { reduxForm, InjectedFormProps, formValueSelector } from "redux-form";
import QrReadingModal from "../qrReadingModal";
import { ErrorMessage, ModuleHeader } from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from "../form/InputField";
import SelectField from "../form/SelectField";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { Organisation } from "../../reducers/organisation/types";
import { ReduxState } from "../../reducers/rootReducer";
import { TransferAccountTypes } from "../transferAccount/types";

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
  accountType: any[TransferAccountTypes];
  accountTypes: object[];
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
  transferAccountType: string;
}

interface StateProps {
  accountType: any[TransferAccountTypes];
  accountTypes: TransferAccountTypes[];
  businessUsageValue?: string;
  activeOrganisation: Organisation;
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
    const { defaultDisbursement } = this.props;
    this.props.initialize({
      accountType: TransferAccountTypes.USER.toLowerCase(),
      accountTypes: [{ value: "USER", label: "USER" }],
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
      activeOrganisation,
      businessUsageValue,
      transferUsages,
      accountType,
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
          {activeOrganisation !== null &&
          typeof activeOrganisation !== "undefined"
            ? activeOrganisation.token.symbol
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
    const accountTypesList = (accountTypes || []).map(o =>
      Object.values(o).pop()
    );
    if (accountTypesList.includes(TransferAccountTypes.USER)) {
      //  USER
      selectedUserForm = <>{initialDisbursementAmount}</>;
    }
    if (accountTypesList.includes(TransferAccountTypes.CASHIER)) {
      //  CASHIER
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
    if (accountTypesList.includes(TransferAccountTypes.VENDOR)) {
      //  VENDOR
      selectedVendorForm = (
        <div>
          {businessUsage}
          <InputField name="transferAccountName" label={"Store Name"} />
        </div>
      );
    }
    if (accountTypesList.includes(TransferAccountTypes.TOKENAGENT)) {
      //  SUPERVENDOR
      selectedTokenAgentForm = <></>;
    }

    return (
      <div>
        <ModuleHeader>Create a {accountType} account</ModuleHeader>

        <div style={{ padding: "1em" }}>
          <form onSubmit={this.props.handleSubmit}>
            <SelectField
              name="accountType"
              label={"Account Type"}
              options={Object.keys(TransferAccountTypes)}
              hideNoneOption={true}
            />
            <InputField
              {...accountTypes}
              name="accountTypes"
              label={"Account Types"}
              isMultipleChoice={true}
              options={validRoles}
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
              buttonText="Submit"
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
  (state: ReduxState): StateProps => {
    const selector = formValueSelector("createUser");
    // @ts-ignore
    console.log(state.organisations.byId[state.login.organisationId]);
    return {
      accountType: selector(state, "accountType"),
      accountTypes: selector(state, "accountTypes"),
      businessUsageValue: selector(state, "businessUsage"),
      // @ts-ignore
      activeOrganisation: state.organisations.byId[state.login.organisationId],
      defaultDisbursement:
        // @ts-ignore
        state.organisations.byId[state.login.organisationId]
          .default_disbursement / 100,
      // @ts-ignore
      validRoles:
        state.organisations.byId[state.login.organisationId].valid_roles
    };
  }
)(CreateUserFormReduxForm);
