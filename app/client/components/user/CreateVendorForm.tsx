import React from "react";

import {formValueSelector, reduxForm, InjectedFormProps} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from '../form/InputField'
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
        <InputField name="publicSerialNumber" label={isCashierAccountValue ? 'Cashier Phone Number' : 'Phone Number or ID'} isRequired>
          <QrReadingModal
            updateData={ (data: string) =>  this.setSerialNumber(data) }
          />
        </InputField>
      )
    } else {
      uniqueIdentifierInput = <InputField name="blockchainAddress" label='Bitcoin Address' isRequired />
    }

    const cashierAccount = <InputField name="isCashierAccount" type="checkbox" label={'Create Cashier Account'} />;

    if (isCashierAccountValue) {
      vendorInput = (
        <div>
          <div>
            To create a cashier account, enter the <strong>vendor's</strong> phone and pin.
          </div>
          <InputField name="existingVendorPhone" label={'Vendor Phone Number'} />
          <InputField name="existingVendorPin" type="password" label={'Vendor PIN'} />
        </div>
      )
    } else {
      vendorInput = (
        <div>
          <InputField name="transferAccountName" label={'Store Name'} />
          <InputField name="location" label={'Address'} />
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

            <InputField name="firstName" label={'First Name'} />
            <InputField name="lastName" label={'Last Name'} />

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

