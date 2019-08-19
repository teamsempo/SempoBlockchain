import React from 'react';
import { connect } from 'react-redux';

import styled, {ThemeProvider} from 'styled-components';
import {UPDATE_ACTIVE_STEP, uploadDocument} from "../../reducers/businessVerificationReducer";
import DateTime from "../dateTime.jsx";

import { DefaultTheme } from "../theme";
import AsyncButton from "../AsyncButton.jsx";
import LoadingSpinner from "../loadingSpinner.jsx";

const UploadButton = function(props) {
  return(
    <TheRealInputButton>
      Upload File
      <InputTrigger
          type="file"
          onChange={props.handleFileChange}
      />
    </TheRealInputButton>
  )
};

const ErrorMessage = function(props) {
  var error = props.input + '_val';
  var error_message = props.input + '_val_msg';

  return(
    <div style={{display: (props.state[error]) ? 'none' : 'flex', color: 'red'}}>{props.state[error_message]}</div>
  )
};

const mapStateToProps = (state) => {
  return {
    business: state.businessVerification.businessVerificationState,
    uploadState: state.businessVerification.uploadDocumentStatus,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    uploadDocument: (body) => dispatch(uploadDocument({body})),
    nextStep: () => dispatch({type: UPDATE_ACTIVE_STEP, activeStep: 2}),
    backStep: () => dispatch({type: UPDATE_ACTIVE_STEP, activeStep: 0})
  };
};

class BusinessDocuments extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      reference: null,
    };
    this.isValidated = this.isValidated.bind(this);
  }

  handleFileChange(event, ref) {
    if (this.props.uploadState.isRequesting) {
      // only one upload at a time
      return
    }

    let document = event.target.files[0];

    if (document) {

      let reader = new FileReader();

      reader.onloadend = () => {
        this.setState({reference: ref});
        this.props.uploadDocument({document: document, reference: ref, kyc_application_id: this.props.business.id});
      };

      reader.readAsDataURL(document);
    }
  }

  _generateDocumentList(documents, reference) {
    return documents.filter(document => document.reference === reference).map((document, idx) => {
      return(
        <DocumentWrapper key={idx}>
          <SVG src="/static/media/document.svg"/>
          <div>
            <DocumentTitle>{document.user_filename}</DocumentTitle>
            <DateTime created={document.created}/>
          </div>
        </DocumentWrapper>
      )
    })
  }

  isValidated() {
    const validateNewInput = this._validateData(this.props.business); // run the new input against the validator

    if (Object.keys(validateNewInput).every((k) => { return validateNewInput[k] === true })) {
      this.props.nextStep()
    } else {
      // if anything fails then update the UI validation state but NOT the UI Data State
      this.setState(Object.assign(validateNewInput, this._validationErrors(validateNewInput)));
    }
  }

  _validateData(data) {
    return  {
      company_documents_val: data.uploaded_documents.filter(document => document.reference === 'company').length > 0,
      owner_documents_val: data.uploaded_documents.filter(document => document.reference === 'owners').length > 0,
    }
  }

  _validationErrors(val) {
    const errMsgs = {
      company_documents_val_msg: val.company_documents_val ? '' : 'You must upload at least one company document',
      owner_documents_val_msg: val.owner_documents_val ? '' : 'You must upload at least one owner document',
    };
    return errMsgs;
  }

  render() {
    let { business, uploadState } = this.props;

    if (business.uploaded_documents !== null && business.uploaded_documents.length > 0) {
      var companyDocuments = this._generateDocumentList(business.uploaded_documents, 'company');
      var ownerDocuments = this._generateDocumentList(business.uploaded_documents, 'owners');
    } else {
      companyDocuments = null;
      ownerDocuments = null;
    }

    let documentLoading = uploadState.isUploading ? <DocumentWrapper style={{justifyContent: 'center'}}><LoadingSpinner/></DocumentWrapper> : null;
    let companyDocumentLoading = this.state.reference === 'company' ? documentLoading : null;
    let ownerDocumentLoading = this.state.reference === 'owners' ? documentLoading : null;

    return(
      <div>
        <h3>Company Identification</h3>
        <SecondaryText>Please provide the Articles of Incorporation and/or other Proof of Ownership for the company. This will be either one or multiple documents depending on your location and business structure.</SecondaryText>
        {companyDocumentLoading}
        {companyDocuments}
        <UploadButton handleFileChange={(e) => this.handleFileChange(e, 'company')}/>
        <ErrorMessage state={this.state} input={'company_documents'}/>

        <h3>Identification of Beneficial Owners</h3>
        <SecondaryText>Please provide a Passport or Driver’s License for each shareholder that holds 25% or more of the company. If uploading a non-Passport document, please provide a photo of the front and back.</SecondaryText>
        {ownerDocumentLoading}
        {ownerDocuments}
        <UploadButton handleFileChange={(e) => this.handleFileChange(e, 'owners')}/>
        <ErrorMessage state={this.state} input={'owner_documents'}/>

        <ThemeProvider theme={DefaultTheme}>
          <div>
            <AsyncButton buttonText={'Back'} onClick={this.props.backStep}/>
            <AsyncButton buttonText={'Next'} onClick={this.isValidated}/>
          </div>
        </ThemeProvider>

      </div>
    );
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BusinessDocuments);

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
  color: #FFF;
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
  box-shadow: 0px 2px 0px 0 rgba(51,51,79,.08);
  font-size: 1em;
  font-weight: 400;
  text-transform: uppercase;
  -webkit-letter-spacing: .025em;
  -moz-letter-spacing: .025em;
  -ms-letter-spacing: .025em;
  letter-spacing: .025em;
  text-decoration: none;
  -webkit-transition: all .15s ease;
  transition: all .15s ease;
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