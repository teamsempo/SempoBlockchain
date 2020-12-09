import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

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
    //todo: this needs to be updated as account type no longer handled via URL
    // if (this.props.is_vendor === true) {
    //   var transfer_account_type = 'vendor'
    // } else {
    //   transfer_account_type = window.BENEFICIARY_TERM_PLURAL.toLowerCase()
    // }

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

  render() {
    if (this.props.button) {
      return (
        <TheRealInputButton>
          <span>{this.props.uploadButtonText}</span>
          <InputTrigger
            type="file"
            onChange={e => this.handleFileChange(e)}
            aria-label="Upload File"
          />
        </TheRealInputButton>
      );
    }

    return (
      <div style={{ display: "flex" }}>
        <InputButtonWrapper>
          <InputButton>
            <span>{this.props.uploadButtonText}</span>
            <InputTrigger
              type="file"
              onChange={e => this.handleFileChange(e)}
              aria-label="Upload File"
            />
          </InputButton>
        </InputButtonWrapper>
      </div>
    );
  }
}

export default connect(
  null,
  mapDispatchToProps
)(UploadButton);

const TheRealInputButton = styled.label`
  background-color: rgb(247, 250, 252);
  color: rgb(184, 197, 207);
  margin: 0;
  line-height: 25px;
  height: 25px;
  position: relative;
  align-items: center;
  justify-content: center;
  outline: none;
  border: 0;
  white-space: nowrap;
  display: inline-block;
  padding: 0 14px;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  font-size: 1em;
  font-weight: 400;
  text-transform: uppercase;
  -webkit-letter-spacing: 0.025em;
  -moz-letter-spacing: 0.025em;
  -ms-letter-spacing: 0.025em;
  letter-spacing: 0.025em;
  text-decoration: none;
  -webkit-transition: all 0.15s ease;
  transition: all 0.15s ease;
  &:hover {
    background-color: #fcfeff;
  }
`;

const InputButtonWrapper = styled.div`
  display: inline-block;
  overflow: hidden;
  //border: 2px dashed #e8e8e8;
  padding: 5px;
  //margin: 10px;
  border-radius: 6px;
`;

const InputButton = styled.label`
  width: 100%;
  height: 100%;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
`;

const InputTrigger = styled.input`
  width: 0.1px;
  height: 0.1px;
  opacity: 0;
  overflow: hidden;
  position: absolute;
  z-index: -1;
`;
