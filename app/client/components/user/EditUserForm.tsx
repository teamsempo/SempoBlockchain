import * as React from "react";
import { connect } from "react-redux";

import { reduxForm, InjectedFormProps, formValueSelector } from "redux-form";

import { GenderTypes } from "./types";
import {
  Wrapper,
  ModuleBox,
  ModuleHeader,
  TopRow,
  ButtonWrapper,
  Row,
  SubRow
} from "../styledElements";
import AsyncButton from "./../AsyncButton.jsx";
import ProfilePicture from "../profilePicture.jsx";
import GetVerified from "../GetVerified.jsx";

import InputField from "../form/InputField";
import SelectField from "../form/SelectField";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { ReduxState } from "../../reducers/rootReducer";
import { TransferAccountTypes } from "../transferAccount/types";
import QrReadingModal from "../qrReadingModal.jsx";
import { replaceUnderscores } from "../../utils";

export interface IEditUser {
  firstName?: string;
  lastName?: string;
  publicSerialNumber?: string;
  phone?: string;
  bio?: string;
  referredBy?: string;
  location?: string;
  businessUsage?: string;
  usageOtherSpecific?: string;
  oneTimeCode: number;
  failedPinAttempts: number;
  accountType: TransferAccountTypes;
  [key: string]: any;
}

interface OuterProps {
  users: any;
  selectedUser: any;
  transferUsages: TransferUsage[];
  onResetPin: () => void;
  onDeleteUser: () => void;
}

interface StateProps {
  accountType: TransferAccountTypes;
  businessUsageValue?: string;
}

type Props = OuterProps & StateProps;

interface attr_dict {
  [key: string]: string;
}

const validate = (values: IEditUser) => {
  const errors: any = {};

  if (!values.phone && !values.publicSerialNumber) {
    errors.phone = "Must provide either phone number or ID number";
  }

  return errors;
};

class EditUserForm extends React.Component<
  InjectedFormProps<IEditUser, Props> & Props
> {
  _updateForm() {
    let account_type;
    let { selectedUser, transferUsages } = this.props;
    let transferUsage = transferUsages.filter(
      t => t.id === selectedUser.business_usage_id
    )[0];
    let transferUsageName = transferUsage && transferUsage.name;
    let customAttributes = selectedUser && selectedUser.custom_attributes;

    if (selectedUser.is_beneficiary) {
      account_type = TransferAccountTypes.USER;
    } else if (selectedUser.is_vendor) {
      account_type = TransferAccountTypes.VENDOR;
    } else if (selectedUser.is_tokenagent) {
      account_type = TransferAccountTypes.TOKENAGENT;
    } else if (selectedUser.is_groupaccount) {
      account_type = TransferAccountTypes.GROUPACCOUNT;
    }

    let custom_attr_keys = customAttributes && Object.keys(customAttributes);
    let attr_dict = {};
    custom_attr_keys.map(key => {
      (attr_dict as attr_dict)[key] = customAttributes[key];
      return attr_dict;
    });

    this.props.initialize({
      firstName: selectedUser.first_name,
      lastName: selectedUser.last_name,
      publicSerialNumber: selectedUser.public_serial_number,
      phone: selectedUser.phone,
      location: selectedUser.location,
      accountType: account_type,
      oneTimeCode: selectedUser.one_time_code,
      failedPinAttempts: selectedUser.failed_pin_attempts,
      businessUsage: transferUsageName,
      ...attr_dict
    });
  }

  componentDidMount() {
    this._updateForm();
  }

  componentDidUpdate(prevProps: OuterProps, prevState: IEditUser): void {
    if (prevProps.selectedUser !== this.props.selectedUser) {
      this._updateForm();
    }
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
      selectedUser,
      transferUsages,
      businessUsageValue,
      users
    } = this.props;
    let transferUsage = transferUsages.filter(
      t => t.id === selectedUser.business_usage_id
    )[0];

    let accountTypes = Object.keys(TransferAccountTypes);
    let customAttributes = selectedUser && selectedUser.custom_attributes;
    let businessUsageName = transferUsage && transferUsage.name;

    let profilePicture = null;
    let custom_attribute_list = null;
    let businessUsage = null;
    if (customAttributes) {
      if (customAttributes.profile_picture) {
        profilePicture = (
          // @ts-ignore
          <ProfilePicture
            label={"Profile Picture:"}
            roll={selectedUser.custom_attributes.profile_picture.roll}
            url={selectedUser.custom_attributes.profile_picture.url}
          />
        );
      } else {
        profilePicture = null;
      }

      custom_attribute_list = Object.keys(customAttributes).map(key => {
        if (key === "gender") {
          return (
            <SubRow key={key}>
              <SelectField
                name={key}
                label={replaceUnderscores(key)}
                options={Object.keys(GenderTypes)}
                hideNoneOption={true}
              />
            </SubRow>
          );
        } else if (!customAttributes[key].uploaded_image_id) {
          return (
            <SubRow key={key}>
              <InputField name={key} label={replaceUnderscores(key)} />
            </SubRow>
          );
        }
      });
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

    return (
      <div style={{ display: "flex", flexDirection: "column" }}>
        <form onSubmit={this.props.handleSubmit}>
          <ModuleBox>
            <Wrapper>
              <TopRow>
                <ModuleHeader>DETAILS</ModuleHeader>
                <ButtonWrapper>
                  {/*
                  // @ts-ignore */}
                  <AsyncButton
                    type="submit"
                    miniSpinnerStyle={{ height: "10px", width: "10px" }}
                    buttonStyle={{
                      display: "inline-flex",
                      fontWeight: "400",
                      margin: "0em",
                      lineHeight: "25px",
                      height: "25px"
                    }}
                    isLoading={users.editStatus.isRequesting}
                    buttonText="SAVE"
                  />
                </ButtonWrapper>
              </TopRow>
              <Row>
                <SubRow>
                  <InputField
                    name="firstName"
                    label="Given Name(s)"
                    isRequired
                  />
                </SubRow>
                <SubRow>
                  <InputField name="lastName" label="Family/Surname" />
                </SubRow>
                <SubRow>
                  <InputField
                    name="phone"
                    label={"Phone Number"}
                    isPhoneNumber
                  />
                </SubRow>
              </Row>
              <Row>
                <SubRow>
                  <InputField name="publicSerialNumber" label={"ID Number"}>
                    {/*
                  // @ts-ignore */}
                    <QrReadingModal
                      updateData={(data: string) => this.setSerialNumber(data)}
                    />
                  </InputField>
                </SubRow>
                <SubRow>
                  <InputField name="location" label="Location" />
                </SubRow>
                <SubRow>
                  <SelectField
                    name="accountType"
                    label="Account Type"
                    options={accountTypes}
                    hideNoneOption={true}
                    isLowercase={false}
                  />
                </SubRow>
              </Row>
              <Row>
                {selectedUser.one_time_code !== "" ? (
                  <SubRow>
                    <InputField
                      disabled={true}
                      name="oneTimeCode"
                      label="One Time Code"
                    />
                  </SubRow>
                ) : null}
                <SubRow>
                  <InputField
                    name="failedPinAttempts"
                    label="Failed Pin Attempts"
                    disabled={true}
                  >
                    {/*
                    // @ts-ignore */}
                    <AsyncButton
                      type="button"
                      onClick={this.props.onResetPin}
                      miniSpinnerStyle={{ height: "10px", width: "10px" }}
                      buttonStyle={{
                        display: "inline-flex",
                        fontWeight: "400",
                        margin: "0em",
                        lineHeight: "25px",
                        height: "25px"
                      }}
                      isLoading={users.pinStatus.isRequesting}
                      buttonText="Reset Pin"
                    />
                  </InputField>
                </SubRow>
                <SubRow>
                  <InputField name="referredBy" label="Referred By" />
                </SubRow>
              </Row>
              <Row>
                <SubRow>
                  {/*
                    // @ts-ignore */}
                  <GetVerified userId={selectedUser.id} />
                </SubRow>
                <SubRow>
                  {/*
                  // @ts-ignore */}
                  <AsyncButton
                    type="button"
                    onClick={this.props.onDeleteUser}
                    miniSpinnerStyle={{ height: "10px", width: "10px" }}
                    buttonStyle={{
                      display: "inline-flex",
                      fontWeight: "400",
                      margin: "0em",
                      lineHeight: "25px",
                      height: "25px"
                    }}
                    isLoading={users.deleteStatus.isRequesting}
                    buttonText="Delete User"
                  />
                </SubRow>
              </Row>
            </Wrapper>
          </ModuleBox>

          {Object.keys(customAttributes).length >= 1 || businessUsageName ? (
            <ModuleBox>
              <Wrapper>
                <TopRow>
                  <ModuleHeader>OTHER ATTRIBUTES</ModuleHeader>
                </TopRow>
                <Row style={{ margin: "0em 1em" }}>
                  {custom_attribute_list || null}
                </Row>
                <Row style={{ margin: "0em 1em" }}>
                  <SubRow>{businessUsage || null}</SubRow>
                </Row>
                <Row style={{ margin: "0em 1em" }}>
                  <SubRow>{profilePicture || null}</SubRow>
                </Row>
              </Wrapper>
            </ModuleBox>
          ) : null}
        </form>
      </div>
    );
  }
}

const EditUserFormReduxForm = reduxForm<IEditUser, Props>({
  form: "editUser",
  validate
})(EditUserForm);

export default connect(
  (state: ReduxState): StateProps => {
    const selector = formValueSelector("editUser");
    return {
      accountType: selector(state, "accountType"),
      businessUsageValue: selector(state, "businessUsage")
    };
  }
)(EditUserFormReduxForm);
