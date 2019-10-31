import React from "react";

import {Field, formValueSelector, reduxForm, InjectedFormProps} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import TextInput from '../form/TextInput'
import {connect} from "react-redux";
import {ICreateUser} from "./CreateUserForm";

export interface ICreateVendor {
  firstName?: string
  lastName?: string
  blockchainAddress?: string
  publicSerialNumber?: string
  isCashierAccount?: boolean
  existingVendorPhone?: string
  existingVendorPin?: string
  location?: string
  transferAccountName?: string
}

const validate = (values: ICreateVendor) => {
  const errors: any = {};

  if (!values.firstName && !values.isCashierAccount) {
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

interface StateProps {
  isCashierAccountValue: boolean
}

interface OuterProps {
  transferAccountType: string
  users: any
}

type Props = StateProps & OuterProps

class CreateVendorForm extends React.Component<InjectedFormProps<ICreateUser, Props> & Props> {
  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, '');
    this.props.change('publicSerialNumber', cleanedData);
  }

  render() {
    const { handleSubmit, isCashierAccountValue } = this.props;
    let uniqueIdentifierInput;
    let vendorInput;

    if (!window.IS_USING_BITCOIN) {
      uniqueIdentifierInput = (
        <Field name="publicSerialNumber" component={TextInput} type="text" label={isCashierAccountValue ? 'Cashier Phone Number' : 'Phone Number or ID'}>
          <QrReadingModal
            updateData={ (data: string) =>  this.setSerialNumber(data) }
          />
        </Field>
      )
    } else {
      uniqueIdentifierInput = <Field name="blockchainAddress" component={TextInput} type="text" label='Bitcoin Address' />
    }

    const cashierAccount = <Field name="isCashierAccount" component={TextInput} type="checkbox" label={'Create Cashier Account'} />;

    if (isCashierAccountValue) {
      vendorInput = (
        <div>
          <div>
            To create a cashier account, enter the <strong>vendor's</strong> phone and pin.
          </div>
          <Field name="existingVendorPhone" component={TextInput} type="text" label={'Vendor Phone Number'} />
          <Field name="existingVendorPin" component={TextInput} type="password" label={'Vendor PIN'} />
        </div>
      )
    } else {
      vendorInput = (
        <div>
          <Field name="transferAccountName" component={TextInput} type="text" label={'Store Name'} />
          <Field name="location" component={TextInput} type="text" label={'Address'} />
        </div>
      )
    }

    return (
      <div>
        <ModuleHeader>Create a Vendor account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form onSubmit={handleSubmit}>
            {cashierAccount}
            {vendorInput}

            <Field name="firstName" component={TextInput} type="text" label={'First Name'} />
            <Field name="lastName" component={TextInput} type="text" label={'Last Name'} />

            {uniqueIdentifierInput}

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

const CreateVendorReduxForm = reduxForm({
  form: 'createVendor',
  validate
// @ts-ignore
})(CreateVendorForm);

// TODO: can't figure out the typing here...
export default connect(state => {
  const selector = formValueSelector('createVendor');
  const isCashierAccountValue = selector(state, 'isCashierAccount');
  return {
    isCashierAccountValue,
  }
// @ts-ignore
})(CreateVendorReduxForm);

