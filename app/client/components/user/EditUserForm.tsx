import React, { useEffect } from "react";
import { connect } from "react-redux";

import {
  Tooltip,
  Card,
  Button,
  Row,
  Col,
  Form,
  Input,
  Space,
  Select,
  Divider
} from "antd";

import { StopOutlined, RedoOutlined } from "@ant-design/icons";

import { GenderTypes } from "./types";
import ProfilePicture from "../profilePicture";
import GetVerified from "../GetVerified";

import { AdaptedPhoneInput } from "../form/PhoneAntDesign";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { ReduxState } from "../../reducers/rootReducer";
import { Organisation } from "../../reducers/organisation/types";
import QrReadingModal from "../qrReadingModal";
import { replaceUnderscores, toTitleCase } from "../../utils";
import FormValidation from "../form/FormValidation";

const { Option } = Select;

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
  accountTypes: string[];
  [key: string]: any;
}

interface OuterProps {
  transferCard: any;
  users: any;
  selectedUser: any;
  transferUsages: TransferUsage[];
  onResetPin: () => void;
  onDeleteUser: () => void;
  onDisableCard: () => void;
}

interface StateProps {
  activeOrganisation: Organisation;
}

type Props = OuterProps & StateProps & IEditUser;

interface attr_dict {
  [key: string]: string;
}

const EditUserForm = (props: Props) => {
  const [form] = Form.useForm();

  const _updateForm = () => {
    let account_types = [];
    let { selectedUser, transferUsages } = props;
    let transferUsage = transferUsages.filter(
      t => t.id === selectedUser.business_usage_id
    )[0];
    let transferUsageName = transferUsage && transferUsage.name;
    let customAttributes = selectedUser && selectedUser.custom_attributes;

    account_types = Object.values(selectedUser.roles || []);
    account_types = account_types.map((role: any) => role);

    let custom_attr_keys =
      (customAttributes && Object.keys(customAttributes)) || [];
    let attr_dict = {};
    custom_attr_keys.map(key => {
      (attr_dict as attr_dict)[key] = customAttributes[key];
      return attr_dict;
    });

    form.setFieldsValue({
      firstName: selectedUser.first_name,
      lastName: selectedUser.last_name,
      publicSerialNumber: selectedUser.public_serial_number,
      phone: selectedUser.phone,
      location: selectedUser.location,
      accountTypes: account_types,
      oneTimeCode: selectedUser.one_time_code,
      failedPinAttempts: selectedUser.failed_pin_attempts,
      businessUsage: transferUsageName,
      ...attr_dict
    });
  };

  useEffect(() => {
    _updateForm();
  }, [props.selectedUser, props.transferUsages]);

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

  const onFinish = (values: any) => {
    props.onSubmit(values);
  };

  const { selectedUser, transferUsages, users, transferCard } = props;
  let transferUsage = transferUsages.filter(
    t => t.id === selectedUser.business_usage_id
  )[0];

  let validRoles = props.activeOrganisation.valid_roles;
  let customAttributes = selectedUser && selectedUser.custom_attributes;
  let businessUsageName = transferUsage && transferUsage.name;

  let profilePicture = null;
  let custom_attribute_list = null;
  // let businessUsage = null;
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

    custom_attribute_list = Object.keys(customAttributes).map((key, index) => {
      if (key === "gender") {
        return (
          <Col span={8} key={key}>
            <Form.Item
              label={toTitleCase(replaceUnderscores(key))}
              name={key}
              key={index}
            >
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
          </Col>
        );
      } else if (!customAttributes[key].uploaded_image_id) {
        return (
          <Col span={8} key={key}>
            <Form.Item label={toTitleCase(replaceUnderscores(key))} name={key}>
              <Input />
            </Form.Item>
          </Col>
        );
      }
    });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      <Form onFinish={onFinish} layout="vertical" form={form}>
        <br />

        <Card
          title={"User Details"}
          extra={
            <Space>
              <Button
                type="text"
                danger
                onClick={props.onDeleteUser}
                loading={users.deleteStatus.isRequesting}
              >
                Delete
              </Button>
              <Form.Item style={{ margin: 0 }}>
                <Button
                  htmlType="submit"
                  type="primary"
                  loading={users.editStatus.isRequesting}
                >
                  Save
                </Button>
              </Form.Item>
            </Space>
          }
        >
          <Row gutter={24}>
            <Col span={8}>
              <Form.Item
                label="Given Name(s)"
                name="firstName"
                rules={[{ required: true, message: "Please input first name" }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Family/Surname" name="lastName">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
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
            </Col>
          </Row>
          <Row gutter={24}>
            <Col span={8}>
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
                  disabled={
                    selectedUser.transfer_card &&
                    selectedUser.transfer_card.is_disabled
                  }
                  addonAfter={
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <QrReadingModal
                        disabled={
                          selectedUser.transfer_card &&
                          selectedUser.transfer_card.is_disabled
                        }
                        updateData={(data: string) => setSerialNumber(data)}
                      />
                      {selectedUser.public_serial_number ? (
                        <div>
                          <Divider type="vertical" />
                          <Tooltip title="Disable Card">
                            <Button
                              disabled={
                                selectedUser.transfer_card &&
                                selectedUser.transfer_card.is_disabled
                              }
                              loading={transferCard.editStatus.isRequesting}
                              onClick={props.onDisableCard}
                              icon={<StopOutlined translate={""} />}
                              type="link"
                              size={"small"}
                            />
                          </Tooltip>
                        </div>
                      ) : (
                        <></>
                      )}
                    </div>
                  }
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Location" name="location">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
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
            </Col>
          </Row>
          <Row gutter={24}>
            {selectedUser.one_time_code !== "" ? (
              <Col span={8}>
                <Form.Item label="One Time Code" name="oneTimeCode">
                  <Input disabled={true} />
                </Form.Item>
              </Col>
            ) : null}
            <Col span={8}>
              <Form.Item label="Failed Pin Attempts" name="failedPinAttempts">
                <Input
                  disabled={true}
                  addonAfter={
                    <Tooltip title="Reset Pin">
                      <Button
                        loading={users.pinStatus.isRequesting}
                        onClick={props.onResetPin}
                        size={"small"}
                        type={"link"}
                        icon={<RedoOutlined translate={""} />}
                      />
                    </Tooltip>
                  }
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Referred By"
                name="referredBy"
                hasFeedback
                rules={[
                  {
                    validator: (_: any, value: any) =>
                      FormValidation.antPhone(value)
                  }
                ]}
              >
                <AdaptedPhoneInput isPhoneNumber />
              </Form.Item>
            </Col>
          </Row>
          <Row>
            <Col span={8}>
              {/*
                // @ts-ignore */}
              <GetVerified userId={selectedUser.id} />
            </Col>
          </Row>
        </Card>

        <br />

        {Object.keys(customAttributes).length >= 1 || businessUsageName ? (
          <Card title={"Other Attributes"}>
            <Row gutter={24}>{custom_attribute_list || null}</Row>
            {transferUsages.length > 0 ? (
              <Row gutter={24}>
                <Col span={8}>
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
                </Col>
              </Row>
            ) : null}
            <Row gutter={24}>
              <Col span={8}>{profilePicture || null}</Col>
            </Row>
          </Card>
        ) : null}
      </Form>
    </div>
  );
};

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    // @ts-ignore
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

export default connect(mapStateToProps)(EditUserForm);
