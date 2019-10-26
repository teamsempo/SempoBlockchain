import React from "react";

import {reduxForm, InjectedFormProps} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from '../form/InputField'
import SelectField from '../form/SelectField'

export interface ICreateUser {
  firstName?: string
  lastName?: string
  blockchainAddress?: string
  publicSerialNumber?: string
  customInitialDisbursement?: number
  bio?: string
  gender?: string
  location?: string
}

const validate = (values: ICreateUser) => {
  const errors: any = {};
  if (!values.firstName) {
    errors.firstName = 'Missing Name'
  }
  if (window.IS_USING_BITCOIN && !values.blockchainAddress) {
    errors.blockchainAddress = 'Missing Blockchain Address';
  }
  //TODO(admin_create): do verifications that if it's a phone number, it's correctly formatted?
  if (!window.IS_USING_BITCOIN && !values.publicSerialNumber) {
    errors.publicSerialNumber = 'Missing Phone or ID';
  }

  return errors
};

interface OuterProps {
  transferAccountType: string
  users: any
}

class CreateUserForm extends React.Component<InjectedFormProps<ICreateUser, OuterProps> & OuterProps> {
  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, '');
    this.props.change('publicSerialNumber', cleanedData);
  }

  render() {
    let uniqueIdentifierInput;
    let initialDisbursementAmount;

    if (!window.IS_USING_BITCOIN) {
      uniqueIdentifierInput = (
        <InputField name="publicSerialNumber" label={'Phone Number or ID'} isRequired>
          <QrReadingModal
            updateData={ (data: string) =>  this.setSerialNumber(data) }
          />
        </InputField>
      )
    } else {
      uniqueIdentifierInput = <InputField name="blockchainAddress" label='Bitcoin Address' isRequired />
    }

    //TODO(admin_create): set a default for it to be easier for staff? should it be 400 or 40000 if we're giving 400 CICs?
    if (window.MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT > 0) {
      initialDisbursementAmount = <InputField name="customInitialDisbursement" label={'Initial Disbursement Amount'}>
        {window.CURRENCY_NAME}
      </InputField>
    }

    //TODO(admin_create): add business category dropdown
    //TODO(admin_create): add default token
    //TODO(admin_create): add button to send SMS about short codes
    return (
      <div>
        <ModuleHeader>Create a {this.props.transferAccountType} account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form onSubmit={this.props.handleSubmit}>
            {uniqueIdentifierInput}
            <InputField name="firstName" label='Given Name(s)' isRequired />
            <InputField name="lastName" label='Family/Surname' />
            <InputField name="bio" label='Directory Entry' />
            <InputField name="location" label='Location' />
            <SelectField name="gender" label='Gender' options={["Male", "Female", "Other"]} />

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
export default reduxForm({
  form: 'createUser',
  validate
// @ts-ignore
})(CreateUserForm);
