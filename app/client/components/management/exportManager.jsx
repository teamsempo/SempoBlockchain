import React from "react";
import { connect } from "react-redux";
import { Select } from "antd";
const { Option } = Select;

import AsyncButton from "../AsyncButton.jsx";

import { ExportAction } from "../../reducers/export/actions";

import { ErrorMessage, ModuleHeader } from "../styledElements";

const mapStateToProps = state => {
  return {
    export: state.export,
    selectedTransferAccounts: state.transferAccounts.selected
  };
};

const mapDispatchToProps = dispatch => {
  return {
    resetExport: () => dispatch(ExportAction.exportReset()),
    newExport: body => dispatch(ExportAction.exportRequest({ body }))
  };
};

class ExportManager extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      error_message: "",
      date_range: "all",
      includeTransfers: false,
      includeCustomAttributes: false,
      startDate: null,
      endDate: null,
      userType: "selected",
      exportType: "spreadsheet"
    };
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }

  componentWillUnmount() {
    this.resetCreateTransferAccount();
  }

  resetCreateTransferAccount() {
    this.props.resetExport();
  }

  handleSetUserType(value) {
    this.setState({ userType: value });
  }

  handleSetExportType(value) {
    this.setState({ exportType: value });
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.value;
    const name = target.name;

    this.setState({
      [name]: value,
      error_message: ""
    });
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  handleToggle(evt, props) {
    this.setState({ [evt.target.name]: !props });
  }

  attemptNewExport() {
    this.props.newExport({
      export_type: this.state.exportType,
      include_transfers: this.state.includeTransfers,
      include_custom_attributes: this.state.includeCustomAttributes,
      user_type: this.state.userType,
      date_range: this.state.date_range,
      payable_period_start_date: null,
      payable_period_end_date: null,
      selected: this.props.selectedTransferAccounts
    });
  }

  render() {
    let transferToggle = (
      <div>
        <div
          style={{ display: "flex", flexDirection: "row", padding: "1em 0" }}
        >
          <p style={{ margin: "0 1em 0 0" }}>Include transfers?</p>
          <input
            name="includeTransfers"
            type="checkbox"
            checked={this.state.includeTransfers}
            onChange={evt =>
              this.handleToggle(evt, this.state.includeTransfers)
            }
          />
        </div>
        <div
          style={{ display: "flex", flexDirection: "row", padding: "1em 0" }}
        >
          <p style={{ margin: "0 1em 0 0" }}>Include Custom Attributes?</p>
          <input
            name="includeCustomAttributes"
            type="checkbox"
            checked={this.state.includeCustomAttributes}
            onChange={evt =>
              this.handleToggle(evt, this.state.includeCustomAttributes)
            }
          />
        </div>
      </div>
    );

    return (
      <div>
        <ModuleHeader>EXPORT ACCOUNTS</ModuleHeader>
        <div style={{ margin: "1em" }}>
          <div
            style={{ display: "flex", flexDirection: "row", padding: "1em 0" }}
          >
            <p style={{ margin: "0px 1em 0px 0px" }}>Export format:</p>
            <Select
              defaultValue="spreadsheet"
              onChange={val => this.handleSetExportType(val)}
              style={{ width: "150px" }}
            >
              <Option key={"spreadsheet"}> Spreadsheet </Option>
              <Option key={"pdf"}> PDF </Option>
            </Select>
          </div>
          <div
            style={{ display: "flex", flexDirection: "row", padding: "1em 0" }}
          >
            <p style={{ margin: "0px 1em 0px 0px" }}>Participant Types:</p>
            <Select
              defaultValue="Selected"
              onChange={val => this.handleSetUserType(val)}
              style={{ width: "150px" }}
            >
              <Option key={"selected"}> Selected </Option>
              <Option key={"all"}> All </Option>
              <Option key={"beneficiary"}>
                {" "}
                {window.BENEFICIARY_TERM_PLURAL}{" "}
              </Option>
              <Option key={"vendor"}> Vendors </Option>
            </Select>
          </div>

          {this.state.exportType === "spreadsheet" ? transferToggle : null}

          <AsyncButton
            onClick={() => this.attemptNewExport()}
            isLoading={this.props.export.isRequesting}
            buttonStyle={{ display: "flex" }}
            buttonText={<span>Export</span>}
            label={"Export"}
          />
          <ErrorMessage>{this.props.export.error}</ErrorMessage>
          <a
            href={this.props.export.file_url}
            target="_blank"
            style={{
              display: this.props.export.file_url === null ? "none" : ""
            }}
          >
            Didn't automatically download?
          </a>
        </div>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(ExportManager);
