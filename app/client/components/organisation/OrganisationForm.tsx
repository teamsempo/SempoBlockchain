import React, { useState, useEffect } from "react";
import { Form, Button, Input, Select, Switch, Divider } from "antd";
import { PlusOutlined } from "@ant-design/icons";

import { Organisation } from "../../reducers/organisation/types";
import TokenModalForm from "./TokenModalForm";
import { ReduxState } from "../../reducers/rootReducer";

const { Option } = Select;

export interface IOrganisation {
  token?: number;
  organisationName?: string;
  defaultDisbursement: number;
  cardShardDistance: number;
  minimumVendorPayoutWithdrawal: number;
  requireTransferCard: boolean;
  requireMultipleTransferApprovals: boolean;
  countryCode: string;
  accountTypes: string[];
  timezone: string;
  lat: number;
  lng: number;
}

interface OuterProps {
  isoCountries: string[];
  timezones: string[];
  organisations: ReduxState["organisations"];
  tokens: ReduxState["tokens"];
  activeOrganisation: Organisation | any;
  roles: string[];
  onSubmit: any;
  isNewOrg: boolean;
}

const NewOrganisationForm = (props: OuterProps) => {
  const [form] = Form.useForm();
  const [visible, setVisible] = useState(false);
  const {
    tokens,
    organisations,
    activeOrganisation,
    isoCountries,
    timezones,
    roles,
    isNewOrg
  } = props;

  const loading = isNewOrg
    ? organisations.createStatus.isRequesting
    : organisations.editStatus.isRequesting;

  useEffect(() => {
    form.resetFields();
  });

  // isoCountries = ['AD: Andorra', ...]
  let countryCode =
    isoCountries.find(
      (country: string) =>
        country.slice(0, 2) == activeOrganisation.country_code
    ) || "";
  const tokenSymbol =
    activeOrganisation.token &&
    tokens.byId[activeOrganisation.token] &&
    tokens.byId[activeOrganisation.token].symbol;

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={props.onSubmit}
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
              requireMultipleTransferApprovals:
                activeOrganisation.require_multiple_transfer_approvals,
              cardShardDistance: activeOrganisation.card_shard_distance,
              countryCode: countryCode,
              timezone: activeOrganisation.timezone,
              token: activeOrganisation.token,
              lat: activeOrganisation.default_lat,
              lng: activeOrganisation.default_lng
            }
      }
    >
      <Form.Item
        tooltip="The name of your project"
        name="organisationName"
        label="Project Name"
        required={isNewOrg}
        rules={[
          {
            required: isNewOrg
          }
        ]}
      >
        <Input disabled={!isNewOrg} placeholder="ACME Inc." />
      </Form.Item>

      <Form.Item
        tooltip="Select a token to use for this project"
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
          {Object.keys(tokens.byId).map((item, i) => {
            const token = tokens.byId[item];
            return (
              <Option key={i} value={token.id} label={token.name}>
                {token.name} ({token.symbol}) - {token.address}
              </Option>
            );
          })}
        </Select>
      </Form.Item>

      <TokenModalForm visible={visible} onCancel={() => setVisible(false)} />

      <Form.Item
        tooltip="The default country code for this project. Used for phone numbers."
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

      <Form.Item
        tooltip="The default time zone for this project."
        name="timezone"
        label="Default Time Zone"
        required={isNewOrg}
        rules={[
          {
            required: isNewOrg
          }
        ]}
      >
        <Select
          showSearch
          placeholder="Select a timezone"
          optionFilterProp="children"
          filterOption={(input, option: any) =>
            option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
          }
        >
          {timezones.map((item, i) => {
            return (
              <Option key={i} value={item}>
                {item}
              </Option>
            );
          })}
        </Select>
      </Form.Item>

      <Form.Item
        tooltip="The available account types for this project."
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

      <Form.Item
        tooltip="The default disbursement amount for new beneficiaries created in this project"
        name="defaultDisbursement"
        label="Default Disbursement"
      >
        <Input placeholder="0" suffix={tokenSymbol} type="number" />
      </Form.Item>

      <Form.Item
        tooltip="The minimum vendor payout withdrawal amount for this project"
        name="minimumVendorPayoutWithdrawal"
        label="Minimum Vendor Payout Withdrawal"
      >
        <Input placeholder="0" suffix={tokenSymbol} type="number" />
      </Form.Item>

      <Form.Item
        tooltip="The distance to automatically load transfer cards onto vendor phones for this project"
        name="cardShardDistance"
        label="Automatically Load Cards Within"
      >
        <Input placeholder="0" suffix="Km" type="number" />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0 }}>
        <Form.Item
          tooltip="The map latitude"
          name="lat"
          label="Map Latitude"
          style={{ display: "inline-block", width: "calc(50% - 12px)" }}
        >
          <Input placeholder="0" suffix="°" type="number" />
        </Form.Item>
        <span
          style={{
            display: "inline-block",
            width: "24px",
            lineHeight: "32px",
            textAlign: "center"
          }}
        />
        <Form.Item
          tooltip="The map longitude"
          name="lng"
          label="Map Longitude"
          style={{ display: "inline-block", width: "calc(50% - 12px)" }}
        >
          <Input placeholder="0" suffix="°" type="number" />
        </Form.Item>
      </Form.Item>

      <Form.Item
        tooltip="Whether or not to require a transfer card exists when tying a public serial number to beneficiary"
        valuePropName="checked"
        name="requireTransferCard"
        label="Require Transfer Card"
      >
        <Switch />
      </Form.Item>
      <Form.Item
        tooltip="Whether disbursements and transfers require two admins to approve them"
        valuePropName="checked"
        name="requireMultipleTransferApprovals"
        label="Require Multiple Transfer Approvals"
      >
        <Switch />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          Save
        </Button>
      </Form.Item>
    </Form>
  );
};

export default NewOrganisationForm;
