import React from "react";
import { connect } from "react-redux";

import styled, { ThemeProvider } from "styled-components";
import { BusinessVerificationAction } from "../../reducers/businessVerification/actions";
import DateTime from "../dateTime.tsx";

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
    nextStep: () => dispatch(BusinessVerificationAction.updateActiveStep(2)),
    backStep: () => dispatch(BusinessVerificationAction.updateActiveStep(0))
  };
};

class BusinessDocuments extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      reference: null
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
        this.setState({ reference: ref });
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
      if (this.props.isFinal) {
        let business = this.props.business;
        this.props.nextStep();
        this.props.editBusinessProfile({ kyc_status: "PENDING" }, business.id);
      } else {
        this.props.nextStep();
      }
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
    let businessValidation;
    if (this.props.business.account_type === "BUSINESS") {
      businessValidation = {
        company_documents_val:
          data.uploaded_documents.filter(
            document => document.reference === "company"
          ).length > 0
      };
    }

    return {
      ...businessValidation,
      owner_documents_val:
        data.uploaded_documents.filter(
          document => document.reference === "owners"
        ).length > 0
    };
  }

  _validationErrors(val) {
    const errMsgs = {
      company_documents_val_msg: val.company_documents_val
        ? ""
        : "You must upload at least one company document",
      owner_documents_val_msg: val.owner_documents_val
        ? ""
        : "You must upload at least one owner document"
    };
    return errMsgs;
  }

  render() {
    let { business, uploadState } = this.props;

    if (business.uploaded_documents && business.uploaded_documents.length > 0) {
      var companyDocuments = this._generateDocumentList(
        business.uploaded_documents,
        "company"
      );
      var ownerDocuments = this._generateDocumentList(
        business.uploaded_documents,
        "owners"
      );
    } else {
      companyDocuments = null;
      ownerDocuments = null;
    }

    let documentLoading = uploadState.isUploading ? (
      <DocumentWrapper style={{ justifyContent: "center" }}>
        <LoadingSpinner />
      </DocumentWrapper>
    ) : null;
    let companyDocumentLoading =
      this.state.reference === "company" ? documentLoading : null;
    let ownerDocumentLoading =
      this.state.reference === "owners" ? documentLoading : null;

    let isIndividual = business.account_type === "INDIVIDUAL";

    return (
      <div>
        {isIndividual ? null : (
          <div>
            <h3>Company Identification</h3>
            <SecondaryText>
              Please provide the Articles of Incorporation and/or other Proof of
              Ownership for the company. This will be either one or multiple
              documents depending on your location and business structure.
            </SecondaryText>
            {companyDocumentLoading}
            {companyDocuments}
            <UploadButton
              handleFileChange={e => this.handleFileChange(e, "company")}
            />
            <ErrorMessage state={this.state} input={"company_documents"} />
          </div>
        )}

        {isIndividual ? (
          <div>
            <h3>Identification of Individual</h3>
            <SecondaryText>
              Please provide a Passport or Driver’s License. If uploading a
              non-Passport document, please provide a photo of the front and
              back.
            </SecondaryText>
          </div>
        ) : (
          <div>
            <h3>Identification of Beneficial Owners</h3>
            <SecondaryText>
              Please provide a Passport or Driver’s License for each shareholder
              that holds 25% or more of the company. If uploading a non-Passport
              document, please provide a photo of the front and back.
            </SecondaryText>
          </div>
        )}
        {ownerDocumentLoading}
        {ownerDocuments}
        <UploadButton
          handleFileChange={e => this.handleFileChange(e, "owners")}
        />
        <ErrorMessage state={this.state} input={"owner_documents"} />

        <ThemeProvider theme={DefaultTheme}>
          <div>
            <AsyncButton
              buttonText={<span>Back</span>}
              onClick={this.props.backStep}
              label={"Back"}
            />
            <AsyncButton
              buttonText={
                this.props.isFinal ? <span>COMPLETE</span> : <span>Next</span>
              }
              onClick={this.isValidated}
              isLoading={this.props.editStatus.isRequesting}
              label={this.props.isFinal ? "Complete" : "Next"}
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
)(BusinessDocuments);

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
