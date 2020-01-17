import * as React from "react";
import {connect} from "react-redux";

import {reduxForm, InjectedFormProps, formValueSelector, FormSection} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from '../form/InputField'
import SelectField from '../form/SelectField'
import {TransferUsage} from "../../reducers/transferUsage/types";
import {Organisation} from "../../reducers/organisation/types";
import {ReduxState} from "../../reducers/rootReducer";
import {TransferAccountTypes} from "../transferAccount/types";

export interface ICreateUser {
  firstName?: string
  lastName?: string
  publicSerialNumber?: string,
  phone?: string,
  initialDisbursement?: number
  bio?: string
  gender?: string
  location?: string
  businessUsage?: string
  usageOtherSpecific?: string,
  accountType: any[TransferAccountTypes],
}

export interface ICreateVendor {
  firstName?: string
  lastName?: string
  publicSerialNumber?: string
  phone?: string
  isCashierAccount?: boolean
  existingVendorPhone?: string
  existingVendorPin?: string
  location?: string
  transferAccountName?: string
}

export type ICreateUserUpdate = ICreateUser & ICreateVendor

interface OuterProps {
  users: any
  transferUsages: TransferUsage[]
}

interface StateProps {
  accountType: any[TransferAccountTypes],
  businessUsageValue?: string
  organisation: Organisation | null
}

type Props = OuterProps & StateProps

const validate = (values: ICreateUser) => {
  const errors: any = {};

  if (!values.phone && !values.publicSerialNumber) {
    errors.phone = 'Must provide either phone number or ID number'
  }

  return errors
};

class CreateUserForm extends React.Component<InjectedFormProps<ICreateUser, Props> & Props> {
  componentDidMount() {
    this.props.initialize({
      accountType: TransferAccountTypes.USER.toLowerCase(),
      gender: 'female',
      initialDisbursement: window.DEFAULT_INITIAL_DISBURSEMENT / 100 || undefined
    });
  }

  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, '');
    this.props.change('publicSerialNumber', cleanedData);
  }

  optionizeUsages() {
    return this.props.transferUsages.map((transferUsage) => {
      return {
        name: transferUsage.name,
        value: transferUsage.name
      }
    }).concat(
      {
        name: "Other",
        value: "other"
      }
    )
  }

  render() {
    const {organisation, businessUsageValue, transferUsages, accountType} = this.props;

    let accountTypes = Object.keys(TransferAccountTypes);
    let selectedAccountTypeForm;
    let initialDisbursementAmount;
    let businessUsage;

    if (window.DEFAULT_INITIAL_DISBURSEMENT > 0) {
      initialDisbursementAmount = <InputField name="initialDisbursement" label={'Initial Disbursement Amount'}>
        {organisation !== null ? organisation.token.symbol : null}
      </InputField>
    }
    if (transferUsages.length > 0) {
      if (businessUsageValue && businessUsageValue.toLowerCase() === "other") {
        businessUsage = <>
          <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />
          <InputField name="usageOtherSpecific" label='Please specify the category' isRequired isNotOther />
        </>
      } else {
        businessUsage = <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />
      }
    }

    if (accountType === TransferAccountTypes.USER.toLowerCase()) {
    //  USER
      selectedAccountTypeForm =
        <>
        {businessUsage}
        {initialDisbursementAmount}
        </>

    } else if (accountType === TransferAccountTypes.CASHIER.toLowerCase()) {
    //  CASHIER
      selectedAccountTypeForm =
        <div>
          <div>
            To create a cashier account, enter the <strong>vendor's</strong> phone and pin.
          </div>
          <InputField name="existingVendorPhone" label={'Vendor Phone Number'} />
          <InputField name="existingVendorPin" type="password" label={'Vendor PIN'} />
        </div>

    } else if (accountType === TransferAccountTypes.VENDOR.toLowerCase()) {
    //  VENDOR
      selectedAccountTypeForm =
        <div>
          <InputField name="transferAccountName" label={'Store Name'} />
          <InputField name="location" label={'Address'} />
        </div>

    } else if (accountType === TransferAccountTypes.TOKENAGENT.toLowerCase()) {
    //  SUPERVENDOR
      selectedAccountTypeForm =
        <>
        </>

    }

    return (
      <div>
        <ModuleHeader>Create a {accountType} account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form onSubmit={this.props.handleSubmit}>

            <SelectField name="accountType" label={'Account Type'} options={accountTypes} hideNoneOption={true}/>

            <InputField name="publicSerialNumber" label={'ID Number'}>
              {/*
                // @ts-ignore */}
              <QrReadingModal
                updateData={ (data: string) =>  this.setSerialNumber(data) }
              />
            </InputField> <span>or</span>
            <InputField name="phone" label={'Phone Number'} isPhoneNumber />

            <InputField name="firstName" label='Given Name(s)' isRequired />
            <InputField name="lastName" label='Family/Surname' />
            <InputField name="bio" label='Directory Entry' />
            <InputField name="location" label='Location' />
            <SelectField name="gender" label='Gender' options={["Female", "Male", "Other"]} hideNoneOption={true} />

            {selectedAccountTypeForm}

            <ErrorMessage>
              {this.props.users.createStatus.error}
            </ErrorMessage>
            {/*
                // @ts-ignore */}
            <AsyncButton
              type="submit"
              isLoading={this.props.users.createStatus.isRequesting}
              buttonStyle={{display: 'flex'}}
              buttonText="Submit"
            />
          </form>
        </div>
      </div>
    );
  }
}

// TODO: can't figure out the typing here...
const CreateUserFormReduxForm = reduxForm({
  form: 'createUser',
  validate
// @ts-ignore
})(CreateUserForm);

export default connect((state: ReduxState): StateProps => {
  const selector = formValueSelector('createUser');
  return {
    accountType: selector(state, 'accountType'),
    businessUsageValue: selector(state, 'businessUsage'),
    // @ts-ignore
    organisation: state.organisation.data
  }
// @ts-ignore
})(CreateUserFormReduxForm);

