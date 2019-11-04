import React from "react";
import {connect} from "react-redux";

import {reduxForm, InjectedFormProps, formValueSelector} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from '../form/InputField'
import SelectField from '../form/SelectField'
import {TransferUsage} from "../../reducers/transferUsage/types";

export interface ICreateUser {
  firstName?: string
  lastName?: string
  publicSerialNumber?: string,
  phone?: string,
  additionalInitialDisbursement?: number
  bio?: string
  gender?: string
  location?: string
  businessUsage?: string
  usageOtherSpecific?: string
}

interface OuterProps {
  transferAccountType: string
  users: any
  transferUsages: TransferUsage[]
}

interface StateProps {
  businessUsageValue?: string
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
  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, '');
    this.props.change('publicSerialNumber', cleanedData);
  }

  optionizeUsages() {
    return this.props.transferUsages.map((transferUsage) => {
      return {
        name: transferUsage.name,
        value: transferUsage.name.toLowerCase()
      }
    })
  }

  render() {
    let initialDisbursementAmount;
    let businessUsage;

    if (window.MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT > 0) {
      initialDisbursementAmount = <InputField name="additionalInitialDisbursement" label={'Additional Initial Disbursement Amount'}>
        {window.CURRENCY_NAME}
      </InputField>
    }
    if (this.props.transferUsages.length > 0) {
      if (this.props.businessUsageValue && this.props.businessUsageValue === "other") {
        businessUsage = <>
          <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />
          <InputField name="usageOtherSpecific" label='Please specify the category' isRequired />
        </>
      } else {
        businessUsage = <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />
      }
    }

    return (
      <div>
        <ModuleHeader>Create a {this.props.transferAccountType} account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form onSubmit={this.props.handleSubmit}>
            <InputField name="publicSerialNumber" label={'ID Number'}>
              <QrReadingModal
                updateData={ (data: string) =>  this.setSerialNumber(data) }
              />
            </InputField> <span>or</span>
            <InputField name="phone" label={'Phone Number'} isPhoneNumber />
            <InputField name="firstName" label='Given Name(s)' isRequired />
            <InputField name="lastName" label='Family/Surname' />
            <InputField name="bio" label='Directory Entry' />
            <InputField name="location" label='Location' />
            <SelectField name="gender" label='Gender' options={["Male", "Female", "Other"]} />

            {businessUsage}
            {initialDisbursementAmount}

            <ErrorMessage>
              {this.props.users.createStatus.error}
            </ErrorMessage>
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
const CreateUserReduxForm = reduxForm({
  form: 'createUser',
  validate
// @ts-ignore
})(CreateUserForm);

export default connect(state => {
  const selector = formValueSelector('createUser');
  return {
    businessUsageValue: selector(state, 'businessUsage'),
  }
// @ts-ignore
})(CreateUserReduxForm);

