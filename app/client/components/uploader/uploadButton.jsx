import React from "react";
import { connect } from "react-redux";
import { Upload } from "antd";
import { InboxOutlined } from "@ant-design/icons";

const { Dragger } = Upload;

import { SpreadsheetAction } from "../../reducers/spreadsheet/actions";

const mapDispatchToProps = dispatch => {
  return {
    uploadSpreadsheet: payload =>
      dispatch(SpreadsheetAction.uploadSpreadsheetRequest(payload))
  };
};

class UploadButton extends React.Component {
  constructor(props) {
    super(props);
  }

  handleFileChange(event) {
    let spreadsheet = event.target.files[0];

    if (spreadsheet) {
      var preview_id = Math.floor(Math.random() * 100000);

      let reader = new FileReader();

      reader.onloadend = () => {
        this.props.uploadSpreadsheet({
          body: { spreadsheet: spreadsheet, preview_id: preview_id }
        });
      };

      reader.readAsDataURL(spreadsheet);
    }
  }

  customRequest = ({ onSuccess, onError, file }) => {
    const checkInfo = () => {
      setTimeout(() => {
        if (!this.imageDataAsURL) {
          checkInfo();
        } else {
          this.props
            .uploadSpreadsheet({
              body: {
                spreadsheet: file,
                preview_id: Math.floor(Math.random() * 100000)
              }
            })
            .then(() => {
              onSuccess(null, file);
            })
            .catch(() => {
              onError();
            });
        }
      }, 100);
    };

    checkInfo();
  };

  onChange = info => {
    const reader = new FileReader();
    reader.onloadend = obj => {
      this.imageDataAsURL = obj.srcElement.result;
    };
    reader.readAsDataURL(info.file.originFileObj);
  };

  render() {
    let draggerProps = {
      name: "file",
      multiple: false,
      showUploadList: true,
      customRequest: this.customRequest,
      onChange: this.onChange
    };
    return (
      <Dragger {...draggerProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          Click or drag file to this area to upload
        </p>
        <p className="ant-upload-hint">Support for a CSV or XLSX files only.</p>
      </Dragger>
    );
  }
}

export default connect(
  null,
  mapDispatchToProps
)(UploadButton);
