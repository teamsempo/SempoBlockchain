import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import DateTime from "../dateTime.tsx";
import { BusinessVerificationAction } from "../../reducers/businessVerification/actions";

import { DefaultTheme } from "../theme";
import AsyncButton from "../AsyncButton.jsx";
import LoadingSpinner from "../loadingSpinner.jsx";

const UploadButton = function(props) {
  return (
    <TheRealInputButton>
      Upload File
      <InputTrigger type="file" onChange={props.handleFileChange} />
    </TheRealInputButton>
  );
};

const ErrorMessage = function(props) {
  var error = props.input + "_val";
  var error_message = props.input + "_val_msg";

  return (
    <div
      style={{ display: props.state[error] ? "none" : "flex", color: "red" }}
    >
      {props.state[error_message]}
    </div>
  );
};

const mapStateToProps = state => {
  return {
    editStatus: state.businessVerification.editStatus,
    business: state.businessVerification.businessVerificationState,
    uploadState: state.businessVerification.uploadDocumentStatus
  };
};

const mapDispatchToProps = dispatch => {
  return {
    editBusinessProfile: (body, path) =>
      dispatch(
        BusinessVerificationAction.editBusinessVerificationRequest({
          body,
          path
        })
      ),
    uploadDocument: body =>
      dispatch(BusinessVerificationAction.uploadDocumentRequest({ body })),
    backStep: () => dispatch(BusinessVerificationAction.updateActiveStep(3)),
    nextStep: () => dispatch(BusinessVerificationAction.updateActiveStep(5))
  };
};

class BusinessBankDocuments extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      reference: "bank"
    };
    this.isValidated = this.isValidated.bind(this);
  }

  handleFileChange(event, ref) {
    if (this.props.uploadState.isRequesting) {
      // only one upload at a time
      return;
    }

    let document = event.target.files[0];

    if (document) {
      let reader = new FileReader();

      reader.onloadend = () => {
        this.props.uploadDocument({
          document: document,
          reference: ref,
          kyc_application_id: this.props.business.id
        });
      };

      reader.readAsDataURL(document);
    }
  }

  _generateDocumentList(documents, reference) {
    return documents
      .filter(document => document.reference === reference)
      .map((document, idx) => {
        return (
          <DocumentWrapper key={idx}>
            <SVG
              src="/static/media/document.svg"
              alt={"Document " + document.user_filename}
            />
            <div>
              <DocumentTitle>{document.user_filename}</DocumentTitle>
              <DateTime created={document.created} />
            </div>
          </DocumentWrapper>
        );
      });
  }

  isValidated() {
    const validateNewInput = this._validateData(this.props.business); // run the new input against the validator

    if (
      Object.keys(validateNewInput).every(k => {
        return validateNewInput[k] === true;
      })
    ) {
      let business = this.props.business;
      this.props.nextStep();
      this.props.editBusinessProfile({ kyc_status: "PENDING" }, business.id);
    } else {
      // if anything fails then update the UI validation state but NOT the UI Data State
      this.setState(
        Object.assign(
          validateNewInput,
          this._validationErrors(validateNewInput)
        )
      );
    }
  }

  _validateData(data) {
    return {
      bank_documents_val:
        data.uploaded_documents.filter(
          document => document.reference === "bank"
        ).length > 0
    };
  }

  _validationErrors(val) {
    const errMsgs = {
      bank_documents_val_msg: val.bank_documents_val
        ? ""
        : "You must upload at least one bank document"
    };
    return errMsgs;
  }

  render() {
    let { business, uploadState } = this.props;

    if (business.uploaded_documents && business.uploaded_documents.length > 0) {
      var bankDocuments = this._generateDocumentList(
        business.uploaded_documents,
        "bank"
      );
    } else {
      bankDocuments = null;
    }

    let documentLoading = uploadState.isUploading ? (
      <DocumentWrapper style={{ justifyContent: "center" }}>
        <LoadingSpinner />
      </DocumentWrapper>
    ) : null;

    return (
      <div>
        <h3>Upload a bank statement</h3>
        <SecondaryText>
          Please upload your most recent bank statement within the last three
          months. The document must also include your full legal name (or your
          company's) and match the address registered on Sempo. If your bank
          statement has a different address, please also provide a utility bill
          for your registered address.
        </SecondaryText>
        <br />
        <SecondaryText>Please note:</SecondaryText>
        <SecondaryDiv>
          <ul>
            <li>
              This bank statement must correspond to the account you'll be using
              to fund your account
            </li>
            <li>The statement must NOT have a zero balance</li>
            <li>Credit card statements are NOT applicable</li>
            <li>
              Statement must be from a bank; third-party statements are NOT
              acceptable
            </li>
            <li>
              Statement must be from the last three months, and must show one
              full month's worth of transaction activity
            </li>
            <li>
              Your name and address should match your Personal ID (If they do
              not match, please also upload a utility bill or leasing/housing
              contract in order to provide proof of address)
            </li>
            <li>
              If no bank statement is available, please upload a document to
              provide proof of address, and send a message to our team
              at team@withsempo.com for help
            </li>
          </ul>
        </SecondaryDiv>

        {documentLoading}
        {bankDocuments}
        <UploadButton
          handleFileChange={e => this.handleFileChange(e, "bank")}
        />
        <ErrorMessage state={this.state} input={"bank_documents"} />

        <ThemeProvider theme={DefaultTheme}>
          <div>
            <AsyncButton
              buttonText={<span>Back</span>}
              onClick={this.props.backStep}
              label={"Back"}
            />
            <AsyncButton
              buttonText={<span>COMPLETE</span>}
              onClick={this.isValidated}
              isLoading={this.props.editStatus.isRequesting}
              label={"Complete"}
            />
          </div>
        </ThemeProvider>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BusinessBankDocuments);

const SecondaryDiv = styled.div`
  color: #555555;
  font-size: 12px;
  padding-top: 0;
  margin: 0;
  font-weight: 600;
`;

const SecondaryText = styled.p`
  color: #555555;
  font-size: 12px;
  padding-top: 0;
  margin: 0;
  font-weight: 600;
`;

const DocumentTitle = styled.p`
  margin: 0 0 5px 0;
  font-weight: 500;
`;

const DocumentWrapper = styled.div`
  margin: 1em 0;
  padding: 10px;
  display: flex;
  align-items: center;
  border: 1px solid #d5d5d5;
`;

const SVG = styled.img`
  width: 20px;
  padding: 1em 1.5em 1em 1em;
`;

const TheRealInputButton = styled.label`
  background-color: #30a4a6;
  color: #fff;
  margin: 0.5em 0;
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
    background-color: #34b0b3;
  }
`;

const InputTrigger = styled.input`
  width: 0.1px;
  height: 0.1px;
  opacity: 0;
  overflow: hidden;
  position: absolute;
  z-index: -1;
`;
