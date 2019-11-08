import React from "react";

import {formValueSelector, reduxForm, InjectedFormProps} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from '../form/InputField'
import {connect} from "react-redux";

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

interface StateProps {
  isCashierAccountValue: boolean
}

interface OuterProps {
  transferAccountType: string
  users: any
}

type Props = StateProps & OuterProps

const validate = (values: ICreateVendor) => {
  const errors: any = {};

  if (!values.phone && !values.publicSerialNumber) {
    errors.phone = 'Must provide either phone number or ID number'
  }

  return errors
};

class CreateVendorForm extends React.Component<InjectedFormProps<ICreateVendor, Props> & Props> {
  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, '');
    this.props.change('publicSerialNumber', cleanedData);
  }

  render() {
    const { handleSubmit, isCashierAccountValue } = this.props;
    let vendorInput;

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
            <InputField name="isCashierAccount" type="checkbox" label={'Create Cashier Account'} />
            {vendorInput}

            <InputField name="publicSerialNumber" label={'ID Number'}>
              <QrReadingModal
                updateData={ (data: string) =>  this.setSerialNumber(data) }
              />
            </InputField> <span>or</span>
            <InputField name="phone" label={'Phone Number'} isPhoneNumber />
            <InputField name="firstName" label={'First Name'} isRequired={!isCashierAccountValue} />
            <InputField name="lastName" label={'Last Name'} />

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
  return {
    isCashierAccountValue: selector(state, 'isCashierAccount'),
  }
// @ts-ignore
})(CreateVendorReduxForm);

