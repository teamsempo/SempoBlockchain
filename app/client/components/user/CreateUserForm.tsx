import React from "react";

import {reduxForm, InjectedFormProps, formValueSelector} from "redux-form";
import QrReadingModal from "../qrReadingModal";
import {ErrorMessage, ModuleHeader} from "../styledElements";
import AsyncButton from "../AsyncButton";
import InputField from '../form/InputField'
import SelectField from '../form/SelectField'
import {connect} from "react-redux";

export interface ICreateUser {
  firstName?: string
  lastName?: string
  blockchainAddress?: string
  publicSerialNumber?: string
  customInitialDisbursement?: number
  bio?: string
  gender?: string
  location?: string
  businessUsage?: string
  defaultToken?: string
}

//TODO(admin_create): change these types when figure out the format
interface StateProps {
  transferUsages: any[]
  tokens: any[]
}

interface OuterProps {
  transferAccountType: string
  users: any
}

type Props = StateProps & OuterProps

class CreateUserForm extends React.Component<InjectedFormProps<ICreateUser, Props> & Props> {
  setSerialNumber(data: string) {
    const cleanedData = data.replace(/^\s+|\s+$/g, '');
    this.props.change('publicSerialNumber', cleanedData);
  }

  optionizeUsages() {
    return this.props.transferUsages.map((transferUsage) => {
      return {
        name: transferUsage.name,
        value: transferUsage.id
      }
    })
  }

  optionizeTokens() {
    return this.props.tokens.map((token) => {
      return {
        name: token.name,
        value: token.id
      }
    })
  }

  render() {
    let uniqueIdentifierInput;
    let initialDisbursementAmount;

    if (!window.IS_USING_BITCOIN) {
      //TODO(admin_create): do verifications that if it's a phone number, it's correctly formatted?
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

    //TODO(admin_create): add button to send SMS about short codes
    return (
      <div>
        <ModuleHeader>Create a {this.props.transferAccountType} account</ModuleHeader>

        <div style={{padding: '1em'}}>
          <form onSubmit={this.props.handleSubmit}>
            {uniqueIdentifierInput}
            <InputField name="firstName" label='Given Name(s)' isRequired />
            <InputField name="lastName" label='Family/Surname' />
            <SelectField name="defaultToken" label="Default Token" options={this.optionizeTokens()} isRequired />
            <InputField name="bio" label='Directory Entry' />
            <InputField name="location" label='Location' />
            <SelectField name="gender" label='Gender' options={["Male", "Female", "Other"]} />
            <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />

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
// @ts-ignore
})(CreateUserForm);

export default connect(state => {

  //TODO(admin_create): fetch tokens and default transfer usages
  return {
    transferUsages: [],
    tokens: []
  }
// @ts-ignore
})(CreateUserReduxForm);

