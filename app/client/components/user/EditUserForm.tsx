import * as React from "react";
import {connect} from "react-redux";

import {reduxForm, InjectedFormProps, formValueSelector, FormSection} from "redux-form";

import {Wrapper, ModuleBox, ModuleHeader, TopRow, ButtonWrapper, Row, SubRow} from "../styledElements";
import AsyncButton from './../AsyncButton.jsx'

import InputField from '../form/InputField'
import SelectField from '../form/SelectField'
import {TransferUsage} from "../../reducers/transferUsage/types";
import {Organisation} from "../../reducers/organisation/types";
import {ReduxState} from "../../reducers/rootReducer";
import {TransferAccountTypes} from "../transferAccount/types";
import QrReadingModal from "../qrReadingModal.jsx";

export interface IEditUser {
  firstName?: string
  lastName?: string
  publicSerialNumber?: string,
  phone?: string,
  bio?: string
  gender?: string
  referredBy?: string
  location?: string
  businessUsage?: string
  usageOtherSpecific?: string,
  accountType: any[TransferAccountTypes],
}

export interface ICustomAttrs {
  [key: string]: any
}

export type ICreateUserUpdate = IEditUser & ICustomAttrs

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

const validate = (values: IEditUser) => {
  const errors: any = {};

  if (!values.phone && !values.publicSerialNumber) {
    errors.phone = 'Must provide either phone number or ID number'
  }

  return errors
};

class EditUserForm extends React.Component<InjectedFormProps<IEditUser, Props> & Props> {
  componentDidMount() {
    this.props.initialize({
      accountType: TransferAccountTypes.USER.toLowerCase(),
      gender: 'female',
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
    // const {organisation, businessUsageValue, transferUsages, accountType} = this.props;
    //
    let accountTypes = Object.keys(TransferAccountTypes);
    // let selectedAccountTypeForm;
    // let initialDisbursementAmount;
    // let businessUsage;
    //
    // if (window.DEFAULT_INITIAL_DISBURSEMENT > 0) {
    //   initialDisbursementAmount = <InputField name="initialDisbursement" label={'Initial Disbursement Amount'}>
    //     {organisation !== null ? organisation.token.symbol : null}
    //   </InputField>
    // }
    // if (transferUsages.length > 0) {
    //   if (businessUsageValue && businessUsageValue.toLowerCase() === "other") {
    //     businessUsage = <>
    //       <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />
    //       <InputField name="usageOtherSpecific" label='Please specify the category' isRequired isNotOther />
    //     </>
    //   } else {
    //     businessUsage = <SelectField name="businessUsage" label='Business Category' options={this.optionizeUsages()} />
    //   }
    // }
    //
    // if (accountType === TransferAccountTypes.USER.toLowerCase()) {
    // //  USER
    //   selectedAccountTypeForm =
    //     <>
    //     {businessUsage}
    //     {initialDisbursementAmount}
    //     </>
    //
    // } else if (accountType === TransferAccountTypes.CASHIER.toLowerCase()) {
    // //  CASHIER
    //   selectedAccountTypeForm =
    //     <div>
    //       <div>
    //         To create a cashier account, enter the <strong>vendor's</strong> phone and pin.
    //       </div>
    //       <InputField name="existingVendorPhone" label={'Vendor Phone Number'} />
    //       <InputField name="existingVendorPin" type="password" label={'Vendor PIN'} />
    //     </div>
    //
    // } else if (accountType === TransferAccountTypes.VENDOR.toLowerCase()) {
    // //  VENDOR
    //   selectedAccountTypeForm =
    //     <div>
    //       <InputField name="transferAccountName" label={'Store Name'} />
    //       <InputField name="location" label={'Address'} />
    //     </div>
    //
    // } else if (accountType === TransferAccountTypes.TOKENAGENT.toLowerCase()) {
    // //  SUPERVENDOR
    //   selectedAccountTypeForm =
    //     <>
    //     </>
    //
    // }

    return (
      <div style={{display: 'flex', flexDirection: 'column'}}>
        <form onSubmit={this.props.handleSubmit}>
          <ModuleBox>
            <Wrapper>
              <TopRow>
                <ModuleHeader>DETAILS</ModuleHeader>
                <ButtonWrapper>
                {/*
                  // @ts-ignore */}
                  <AsyncButton type="submit" miniSpinnerStyle={{height: '10px', width: '10px'}} buttonStyle={{display: 'inline-flex', fontWeight: '400', margin: '0em', lineHeight: '25px', height: '25px'}} isLoading={this.props.users.editStatus.isRequesting} buttonText="SAVE"/>
                </ButtonWrapper>
              </TopRow>
              <Row style={{margin: '0em 1em'}}>
                <SubRow>
                  <InputField name="firstName" label='Given Name(s)' isRequired />
                </SubRow>
                <SubRow>
                  <InputField name="lastName" label='Family/Surname' />
                </SubRow>
                <SubRow>
                  <InputField name="phone" label={'Phone Number'} isPhoneNumber />
                </SubRow>
              </Row>
              <Row style={{margin: '0em 1em'}}>
                <SubRow>
                  <InputField name="publicSerialNumber" label={'ID Number'}>
                  {/*
                  // @ts-ignore */}
                  <QrReadingModal
                    updateData={ (data: string) =>  this.setSerialNumber(data) }
                  />
                  </InputField>
                </SubRow>
                <SubRow>
                  <InputField name="location" label='Location' />
                </SubRow>
                <SubRow>
                  <SelectField name="accountType" label='Account Type' options={accountTypes} hideNoneOption={true} />
                </SubRow>
              </Row>
              <Row style={{margin: '0em 1em'}}>
              </Row>
            </Wrapper>
          </ModuleBox>
        </form>
      </div>

      //   <div style={{padding: '1em'}}>
      //     <form onSubmit={this.props.handleSubmit}>
      //
      //       <SelectField name="accountType" label={'Account Type'} options={accountTypes} hideNoneOption={true}/>
      //
      //       <InputField name="publicSerialNumber" label={'ID Number'}>
      //         {/*
      //           // @ts-ignore */}
      //         <QrReadingModal
      //           updateData={ (data: string) =>  this.setSerialNumber(data) }
      //         />
      //       </InputField> <span>or</span>
      //       <InputField name="phone" label={'Phone Number'} isPhoneNumber />
      //
      //       <InputField name="firstName" label='Given Name(s)' isRequired />
      //       <InputField name="lastName" label='Family/Surname' />
      //       <InputField name="bio" label='Directory Entry' />
      //       <InputField name="location" label='Location' />
      //       <SelectField name="gender" label='Gender' options={["Female", "Male", "Other"]} hideNoneOption={true} />
      //       <InputField name="referredBy" label={'Referred by user phone number'} isPhoneNumber />
      //
      //       {selectedAccountTypeForm}
      //
      //       <ErrorMessage>
      //         {this.props.users.createStatus.error}
      //       </ErrorMessage>
      //       {/*
      //           // @ts-ignore */}
      //       <AsyncButton
      //         type="submit"
      //         isLoading={this.props.users.createStatus.isRequesting}
      //         buttonStyle={{display: 'flex'}}
      //         buttonText="Submit"
      //       />
      //     </form>
      //   </div>
      // </div>
    );
  }
}

const EditUserFormReduxForm = reduxForm({
  form: 'editUser',
  validate
})(EditUserForm);

export default connect((state: ReduxState): StateProps => {
  const selector = formValueSelector('editUser');
  return {
    accountType: selector(state, 'accountType'),
    businessUsageValue: selector(state, 'businessUsage'),
    organisation: state.organisation.data
  }
  // @ts-ignore
})(EditUserFormReduxForm);

