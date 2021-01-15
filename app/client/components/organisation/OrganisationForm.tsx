import React, { useState, useEffect } from "react";
import { Form, Button, Input, Select, Switch, Divider } from "antd";
import { PlusOutlined } from "@ant-design/icons";

import { Organisation } from "../../reducers/organisation/types";
import TokenModalForm from "./TokenModalForm";

const { Option } = Select;

export interface IOrganisation {
  defaultDisbursement: number;
  cardShardDistance: number;
  mimimumVendorPayoutWithdrawal: number;
  requireTransferCard: boolean;
  countryCode: string;
  accountTypes: string[];
}

interface OuterProps {
  isoCountries: [];
  organisations: any;
  activeOrganisation: Organisation | any;
  roles: [];
  onSubmit: any;
  isNewOrg: boolean;
}

const NewOrganisationForm = (props: OuterProps) => {
  const [form] = Form.useForm();
  const [visible, setVisible] = useState(false);
  const { activeOrganisation, isoCountries, roles, isNewOrg } = props;

  useEffect(() => {
    form.resetFields();
  });

  const onFinish = (values: any) => {
    console.log(values);
  };

  const onCreate = (values: any) => {
    console.log("Received values of form: ", values);
    setVisible(false);
  };

  // isoCountries = ['AD: Andorra', ...]
  let countryCode =
    isoCountries.find(
      (country: string) =>
        country.slice(0, 2) == activeOrganisation.country_code
    ) || "";
  let activeOrganisationToken = activeOrganisation.token.symbol;

  let tokens = ["celo", "eth"];

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={
        isNewOrg
          ? {
              accountTypes: roles
            }
          : {
              organisationName: activeOrganisation.name,
              accountTypes: activeOrganisation.valid_roles,
              defaultDisbursement:
                activeOrganisation.default_disbursement / 100,
              minimumVendorPayoutWithdrawal:
                activeOrganisation.minimum_vendor_payout_withdrawal / 100,
              requireTransferCard: activeOrganisation.require_transfer_card,
              cardShardDistance: activeOrganisation.card_shard_distance,
              countryCode: countryCode,
              token: activeOrganisationToken
            }
      }
    >
      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="The name of your organisation or project"
        name="organisationName"
        label="Organisation Name"
        required={isNewOrg}
        rules={[
          {
            required: isNewOrg
          }
        ]}
      >
        <Input disabled={!isNewOrg} placeholder="ACME Inc." />
      </Form.Item>

      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="Select a token to use for this organisation"
        name="token"
        label="Token"
        required={isNewOrg}
        rules={[
          {
            required: isNewOrg
          }
        ]}
      >
        <Select
          showSearch
          disabled={!isNewOrg}
          placeholder="Select a token"
          optionFilterProp="children"
          filterOption={(input, option: any) =>
            option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
          }
          dropdownRender={menu => (
            <div>
              {menu}
              <Divider style={{ margin: "4px 0" }} />
              <a
                style={{
                  flex: "none",
                  padding: "8px",
                  display: "block",
                  cursor: "pointer"
                }}
                onClick={() => setVisible(true)}
              >
                <PlusOutlined translate={""} /> Add New Token
              </a>
            </div>
          )}
        >
          {tokens.map((item, i) => {
            return (
              <Option key={i} value={item}>
                {item}
              </Option>
            );
          })}
        </Select>
      </Form.Item>

      <TokenModalForm
        visible={visible}
        onCreate={onCreate}
        onCancel={() => setVisible(false)}
      />

      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="The default country code for this organisation. Used for phone numbers."
        name="countryCode"
        label="Default Country Code"
        required={isNewOrg}
        rules={[
          {
            required: isNewOrg
          }
        ]}
      >
        <Select
          showSearch
          placeholder="Select a country"
          optionFilterProp="children"
          filterOption={(input, option: any) =>
            option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
          }
        >
          {isoCountries.map((item, i) => {
            return (
              <Option key={i} value={item}>
                {item}
              </Option>
            );
          })}
        </Select>
      </Form.Item>

      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="The available account types for this organisation."
        name="accountTypes"
        label="Account Types"
      >
        <Select
          mode="multiple"
          showSearch
          placeholder="Select account types"
          optionFilterProp="children"
          filterOption={(input, option: any) =>
            option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
          }
        >
          {roles.map((item, i) => {
            return (
              <Option key={i} value={item}>
                {item}
              </Option>
            );
          })}
        </Select>
      </Form.Item>

      {/*
        // @ts-ignore */}
      <Form.Item
        tooltip="The default disbursement amount for new beneficiaries created in this organisation"
        name="defaultDisbursement"
        label="Default Disbursement"
      >
        <Input placeholder="0" suffix="RCU" type="number" />
      </Form.Item>

      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="The minimum vendor payout withdrawal amount for this organisation"
        name="minimumVendorPayoutWithdrawal"
        label="Minimum Vendor Payout Withdrawal"
      >
        <Input placeholder="0" suffix="RCU" type="number" />
      </Form.Item>

      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="The distance to automatically load transfer cards onto vendor phones for this organisation"
        name="cardShardDistance"
        label="Automatically Load Cards Within"
      >
        <Input placeholder="0" suffix="Km" type="number" />
      </Form.Item>

      {/*
      // @ts-ignore */}
      <Form.Item
        tooltip="Whether or not to require a transfer card for new beneficiaries"
        valuePropName="checked"
        name="requireTransferCard"
        label="Require Transfer Card"
      >
        <Switch />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          Save
        </Button>
      </Form.Item>
    </Form>
  );
};
// @ts-ignore
export default NewOrganisationForm;
