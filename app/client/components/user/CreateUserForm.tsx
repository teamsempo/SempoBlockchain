import React, { useEffect } from "react";
import { connect } from "react-redux";
import { Form, Input, Button, Select } from "antd";

import QrReadingModal from "../qrReadingModal";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { TransferAccountTypes } from "../transferAccount/types";
import { Token } from "../../reducers/token/types";
import { getActiveToken } from "../../utils";
import { ReduxState } from "../../reducers/rootReducer";
import FormValidation from "../form/FormValidation";
import { AdaptedPhoneInput } from "../form/PhoneAntDesign";
import { GenderTypes } from "./types";

const { Option } = Select;

export interface ICreateUser {
  firstName?: string;
  lastName?: string;
  publicSerialNumber?: string;
  phone?: string;
  initialDisbursement?: number;
  bio?: string;
  gender?: string;
  referredBy?: string;
  location?: string;
  businessUsage?: string;
  usageOtherSpecific?: string;
  accountTypes: string[];
}

export interface ICreateVendor {
  firstName?: string;
  lastName?: string;
  publicSerialNumber?: string;
  phone?: string;
  isCashierAccount?: boolean;
  existingVendorPhone?: string;
  existingVendorPin?: string;
  location?: string;
  transferAccountName?: string;
}

export type ICreateUserUpdate = ICreateUser & ICreateVendor;

interface OuterProps {
  onSubmit: (values: ICreateUserUpdate) => void;
  users: any;
  transferUsages: TransferUsage[];
}

interface StateProps {
  activeToken: Token;
  defaultDisbursement: any;
  validRoles: TransferAccountTypes[];
}

type Props = OuterProps & StateProps;

const CreateUserForm = (props: Props) => {
  const [form] = Form.useForm();
  useEffect(() => {
    const { defaultDisbursement, validRoles } = props;
    form.setFieldsValue({
      accountTypes: [validRoles[0]],
      gender: "female",
      initialDisbursement: defaultDisbursement
    });
  }, []);

  const setSerialNumber = (data: string) => {
    const cleanedData = data.replace(/^\s+|\s+$/g, "");
    form.setFieldsValue({ publicSerialNumber: cleanedData });
  };

  const optionizeUsages = () => {
    return props.transferUsages
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
  };
  const onFinish = (values: ICreateUserUpdate) => {
    props.onSubmit(values);
  };

  const {
    activeToken,
    transferUsages,
    defaultDisbursement,
    validRoles
  } = props;
  let initialDisbursementAmount: JSX.Element;

  if (defaultDisbursement > 0) {
    initialDisbursementAmount = (
      <Form.Item label="Initial Disbursement Amount" name="initialDisbursement">
        <Input
          addonAfter={
            activeToken !== null && typeof activeToken !== "undefined"
              ? activeToken.symbol
              : null
          }
        />
      </Form.Item>
    );
  }

  return (
    <div>
      <Form onFinish={onFinish} layout="vertical" form={form}>
        <Form.Item label="Account Types" name="accountTypes">
          <Select mode="multiple">
            {Object.values(validRoles).map((value, index) => {
              return (
                <Option value={value} key={index}>
                  {value}
                </Option>
              );
            })}
          </Select>
        </Form.Item>
        <Form.Item
          label="ID Number"
          name="publicSerialNumber"
          dependencies={["phone"]}
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value && !getFieldValue("phone")) {
                  return Promise.reject(
                    "Must provide either phone number or ID number"
                  );
                }
                return Promise.resolve();
              }
            })
          ]}
        >
          <Input
            addonAfter={
              <QrReadingModal
                updateData={(data: string) => setSerialNumber(data)}
              />
            }
          />
        </Form.Item>
        <span>or</span>
        <Form.Item
          label="Phone Number"
          name="phone"
          valuePropName="value"
          hasFeedback
          dependencies={["publicSerialNumber"]}
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value && !getFieldValue("publicSerialNumber")) {
                  return Promise.reject(
                    "Must provide either phone number or ID number"
                  );
                }
                return FormValidation.antPhone(value);
              }
            })
          ]}
        >
          <AdaptedPhoneInput isPhoneNumber />
        </Form.Item>
        <Form.Item
          label="Given Name(s)"
          name="firstName"
          rules={[{ required: true, message: "Please input first name" }]}
        >
          <Input />
        </Form.Item>
        <Form.Item label="Family/Surname" name="lastName">
          <Input />
        </Form.Item>
        <Form.Item label="Location" name="location">
          <Input />
        </Form.Item>
        <Form.Item label={"Gender"} name={"gender"}>
          <Select>
            {Object.keys(GenderTypes).map((type, index) => {
              return (
                <Option value={type} key={index}>
                  {type}
                </Option>
              );
            })}
          </Select>
        </Form.Item>
        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) =>
            prevValues.accountTypes !== currentValues.accountTypes
          }
        >
          {({ getFieldValue }) =>
            getFieldValue("accountTypes") &&
            getFieldValue("accountTypes").includes("beneficiary") ? (
              <>{initialDisbursementAmount}</>
            ) : null
          }
        </Form.Item>
        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) =>
            prevValues.accountTypes !== currentValues.accountTypes
          }
        >
          {({ getFieldValue }) =>
            getFieldValue("accountTypes") &&
            getFieldValue("accountTypes").includes("cashier") ? (
              <div>
                <div>
                  To create a cashier account, enter the{" "}
                  <strong>vendor's</strong> phone and pin.
                </div>
                <Form.Item
                  label="Vendor Phone Number"
                  name="existingVendorPhone"
                >
                  <Input />
                </Form.Item>
                <Form.Item label="Vendor PIN" name="existingVendorPin">
                  <Input type="password" />
                </Form.Item>
              </div>
            ) : null
          }
        </Form.Item>
        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) =>
            prevValues.accountTypes !== currentValues.accountTypes
          }
        >
          {({ getFieldValue }) =>
            getFieldValue("accountTypes") &&
            (getFieldValue("accountTypes").includes("vendor") ||
              getFieldValue("accountTypes").includes("cashier") ||
              getFieldValue("accountTypes").includes("supervendor")) ? (
              <div>
                {transferUsages.length > 0 ? (
                  <div>
                    <Form.Item name="businessUsage" label="Business Category">
                      <Select>
                        {optionizeUsages().map(
                          (
                            usage: { value: string; name: React.ReactNode },
                            index: string | number | undefined
                          ) => {
                            return (
                              <Option value={usage.value} key={index}>
                                {usage.name}
                              </Option>
                            );
                          }
                        )}
                      </Select>
                    </Form.Item>
                    <Form.Item
                      noStyle
                      shouldUpdate={(prevValues, currentValues) =>
                        prevValues.businessUsage !== currentValues.businessUsage
                      }
                    >
                      {({ getFieldValue }) =>
                        getFieldValue("businessUsage") &&
                        getFieldValue("businessUsage").toLowerCase() ===
                          "other" ? (
                          <Form.Item
                            name="usageOtherSpecific"
                            label="Please specify the category"
                            rules={[
                              {
                                required: true,
                                message: "Please specify the category!"
                              }
                            ]}
                          >
                            <Input />
                          </Form.Item>
                        ) : null
                      }
                    </Form.Item>
                  </div>
                ) : null}
                <Form.Item label="Store Name" name="transferAccountName">
                  <Input />
                </Form.Item>
              </div>
            ) : null
          }
        </Form.Item>
        <Form.Item>
          <Button
            htmlType="submit"
            type="primary"
            loading={props.users.createStatus.isRequesting}
          >
            Submit
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    activeToken: getActiveToken(state),
    defaultDisbursement:
      // @ts-ignore
      state.organisations.byId[state.login.organisationId]
        .default_disbursement / 100,
    validRoles:
      // @ts-ignore
      state.organisations.byId[state.login.organisationId].valid_roles || []
  };
};

export default connect(mapStateToProps)(CreateUserForm);
