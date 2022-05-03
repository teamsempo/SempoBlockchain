import React from "react";
import { connect } from "react-redux";
import { Modal, Select, Form, Button, Checkbox } from "antd";
const { Option } = Select;

import { ExportAction } from "../../../reducers/export/actions";

const mapStateToProps = (state) => {
  return {
    export: state.export,
    selectedTransferAccounts: state.transferAccounts.selected,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    resetExport: () => dispatch(ExportAction.exportReset()),
    newExport: (body) => dispatch(ExportAction.exportRequest({ body })),
  };
};

const ExportModal = (props) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    values["date_range"] = "all";
    if (values["user_type"] === "selected") {
      values["search_string"] = props.search_string;
      values["params"] = props.params;
      values["include_accounts"] = props.include_accounts;
      values["exclude_accounts"] = props.exclude_accounts;
    }
    props.newExport(values);
    props.handleCancel();
  };

  const onFinishFailed = (errorInfo) => {
    console.log("Failed:", errorInfo);
  };

  return (
    <Modal
      title="Export Data"
      visible={props.isModalVisible}
      onOk={props.handleOk}
      onCancel={props.handleCancel}
      footer={[
        <Button key="back" onClick={props.handleCancel}>
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
          htmlType="submit"
          loading={props.export.isRequesting}
          onClick={() => form.submit()}
        >
          Export
        </Button>,
      ]}
    >
      <Form form={form} onFinish={onFinish} onFinishFailed={onFinishFailed}>
        <Form.Item
          name="export_type"
          label="Export Type"
          initialValue={"spreadsheet"}
        >
          <Select style={{ width: "150px" }}>
            <Option key={"spreadsheet"}> Spreadsheet </Option>
            <Option key={"pdf"}> PDF </Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="user_type"
          label="Participant Type"
          initialValue={"all"}
        >
          <Select style={{ width: "150px" }}>
            <Option key={"all"}> All </Option>
            <Option key={"selected"} disabled={!props.hasSelected}>
              {" "}
              Selected{" "}
            </Option>
            <Option key={"beneficiary"}>
              {" "}
              {window.BENEFICIARY_TERM_PLURAL}{" "}
            </Option>
            <Option key={"vendor"}> Vendors </Option>
          </Select>
        </Form.Item>
        <Form.Item
          name="include_transfers"
          label="Include Transfers"
          valuePropName="checked"
        >
          <Checkbox />
        </Form.Item>
        <Form.Item
          name="include_sent_and_received"
          label="Include Amount Sent and Amount Received"
          valuePropName="checked"
        >
          <Checkbox />
        </Form.Item>
        <Form.Item
          name="include_custom_attributes"
          label="Include Custom Attributes"
          valuePropName="checked"
        >
          <Checkbox />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default connect(mapStateToProps, mapDispatchToProps)(ExportModal);
