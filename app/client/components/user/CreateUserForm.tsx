import React from "react";

import {Field, reduxForm, InjectedFormProps} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import TextInput from '../form/TextInput'

export interface ICreateUser {
  firstName?: string
  lastName?: string
  blockchainAddress?: string
  publicSerialNumber?: string
  customInitialDisbursement?: number
}

const validate = (values: ICreateUser) => {
  const errors: any = {};
  if (!values.firstName) {
    errors.firstName = 'Missing Name'
  }
  if (window.IS_USING_BITCOIN && !values.blockchainAddress) {
    errors.blockchainAddress = 'Missing Blockchain Address';
  }
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
        <Field name="publicSerialNumber" component={TextInput} type="text" label={'Phone Number or ID'}>
          <QrReadingModal
            updateData={ (data: string) =>  this.setSerialNumber(data) }
          />
        </Field>
      )
    } else {
      uniqueIdentifierInput = <Field name="blockchainAddress" component={TextInput} type="text" label='Bitcoin Address' />
    }


    if (window.MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT > 0) {
      initialDisbursementAmount = <Field name="customInitialDisbursement" component={TextInput} type="text" label={'Initial Disbursement Amount'}>
        {window.CURRENCY_NAME}
      </Field>
    }

    return (
      <div>
        <ModuleHeader>Create a {this.props.transferAccountType} account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form onSubmit={this.props.handleSubmit}>
            <Field name="firstName" component={TextInput} type="text" label={'First Name'} />
            <Field name="lastName" component={TextInput} type="text" label={'Last Name'} />
            {uniqueIdentifierInput}
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
