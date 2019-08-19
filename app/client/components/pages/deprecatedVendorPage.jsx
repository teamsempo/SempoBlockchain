import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { Input, StyledButton, ErrorMessage } from '../styledElements'

import { checkQrCode, transferQrCode } from '../../reducers/qrCodeReducer'

import LoadingSpinner from "../loadingSpinner.jsx";
import VendorAuth from '../auth/vendorAuth.jsx'


const mapStateToProps = (state) => {
  return {
    loggedIn: (state.login.vendorId != null),
    qrCodeCheck: state.qrCodeCheck,
    qrCodeTransfer: state.qrCodeTransfer,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    checkQrCode: (payload) => dispatch(checkQrCode(payload)),
    transferQrCode: (payload) => dispatch(transferQrCode(payload))
  };
};

class deprecatedVendorPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
        delay: 0,
        QRCode: '',
        transfer_amount: '',
        pin: '',
        beneficiary: '',
        amount_missing: false,
        checking_qr: false,
        missing_pin: false,
        incorrect_pin: false,
        invalid_qr: false,
        qr_scanner: false,
        legacyMode: false,
    };
    this.handleScan = this.handleScan.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handlePinChange = this.handlePinChange.bind(this);
  }

  componentWillReceiveProps(nextProps) {
    this.setState({checking_qr: (nextProps.qrCodeCheck.isRequesting)});
    this.setState({invalid_qr: (nextProps.qrCodeCheck.error)});
    this.setState({incorrect_pin: (nextProps.qrCodeTransfer.error)});
    this.setState({beneficiary: (nextProps.qrCodeTransfer.data)})
  }

  handleChange(event) {
    this.setState({transfer_amount: event.target.value});
  }

  handlePinChange(event) {
    this.setState({pin: event.target.value});
  }

  handleCheckQrCode(data) {
    console.log(data)
    this.props.checkQrCode({'qr_data': data, 'transfer_amount': this.state.transfer_amount * 100});
  }

  handleScan(data){
    if (this.state.QRCode != data && data && !isNaN(data)) {
        this.setState({
          QRCode: data
        });
        this.handleCheckQrCode(data);
    }
  }

  handleError(err){
    console.error(err);
    this.setState({legacyMode: true})
  }

  handleQrTransfer(){
    if (this.state.pin.length < 4) {
      this.setState({missing_pin: true});
      return
    }
    this.setState({missing_pin: false});
    this.props.transferQrCode({'qr_data': this.state.QRCode, 'transfer_amount': this.state.transfer_amount * 100, 'pin': this.state.pin})
  }

  onConfirmTransfer() {
      this.handleQrTransfer()
  }

  onNewTransfer() {
      // resets state to default
      this.setState({
        QRCode: '',
        transfer_amount: '',
        pin: '',
        beneficiary: '',
        amount_missing: false,
        checking_qr: false,
        missing_pin: false,
        incorrect_pin: false,
        invalid_qr: false,
        qr_scanner: false,
        confirm_transfer: false,
        transfer_status: false,
        legacyMode: false
      });
  }

  checkAmount() {
    if (this.state.transfer_amount.length < 1) {
      this.setState({amount_missing: true});
      return
    }
    this.setState({amount_missing: false, qr_scanner: true});
  }

  onAmountClick(){
    this.checkAmount()
  }

  handleImageUpload(){
      // this.refs.qrReader1.openImageDialog()
  }

  onClick(){
      this.handleImageUpload()
  }

  render() {

    if (this.state.incorrect_pin) {
      var error_message = 'Incorrect Pin. Try Again.'
    } else if (this.state.missing_pin) {
      error_message = 'Missing Pin. Enter 4 Digit Pin.'
    } else if (this.state.invalid_qr) {
      error_message = this.state.invalid_qr
    } else if (this.state.amount_missing) {
      error_message = 'Enter a purchase transfer_amount'
    } else if (this.props.qrCodeCheck.loaded && !this.props.qrCodeCheck.data.sufficient_funds) {
      error_message = 'Customer has insufficient funds'
    } else {
      error_message = ''
    }


     if (this.props.loggedIn && this.props.qrCodeTransfer.success) {
          return(
              <WrapperDiv>
                  <h2>TRANSFER SUCCESSFUL</h2>
                  <p>You received {this.state.transfer_amount} from {this.props.qrCodeCheck.data.first_name} {this.props.qrCodeCheck.data.last_name}</p>

                  <div>
                      <StyledButton onClick={() => this.onNewTransfer()}>New Transfer</StyledButton>
                  </div>

               </WrapperDiv>
          )
     } else if (this.props.loggedIn && this.props.qrCodeCheck.data.sufficient_funds) {
          return(
              <WrapperDiv>
                  <h2>ENTER PIN</h2>
                  <p>Ask {this.props.qrCodeCheck.data.first_name} {this.props.qrCodeCheck.data.last_name} to enter their private pin to confirm transfer of ${this.state.transfer_amount}.00</p>

                  <div>
                      <Input type="text"
                             onChange={this.handlePinChange}
                             placeholder="Enter Pin"
                             value={this.state.pin}
                             maxLength={4}
                      />
                      <StyledButton onClick={() => this.onConfirmTransfer()}>Confirm Transfer</StyledButton>
                  </div>

                  <ErrorMessage>
                        {error_message}
                  </ErrorMessage>

               </WrapperDiv>
          )
     } else if (this.props.loggedIn && this.state.checking_qr) {
          return (
              <WrapperDiv>
                  <h2>CHECKING QR CODE</h2>
                  <LoadingSpinner/>
               </WrapperDiv>
          )
     } else if (this.props.loggedIn && this.state.legacyMode) {
          return (
               <WrapperDiv>
                  <h2>UPLOAD QR CODE</h2>

                  <div style={{width: '100%', maxWidth: '400px'}}>
                      {/*<QrReader*/}
                          {/*ref="qrReader1"*/}
                          {/*legacyMode={this.state.legacyMode}*/}
                          {/*delay={this.state.delay}*/}
                          {/*onError={this.handleError}*/}
                          {/*onScan={this.handleScan}*/}
                          {/*style={{width: '100%', margin: 'auto'}}*/}
                      {/*/>*/}
                  </div>

                  <div>
                      <StyledButton onClick={() => this.onClick()}>Upload Image</StyledButton>
                  </div>

                  <ErrorMessage>
                        {error_message}
                  </ErrorMessage>

               </WrapperDiv>
          )
     } else if (this.props.loggedIn && this.state.qr_scanner) {
          return (
              <WrapperDiv>
                  <h2>SCAN QR CODE</h2>

                  <div style={{width: '100%', maxWidth: '400px'}}>
                      {/*<QrReader*/}
                          {/*legacyMode={this.state.legacyMode}*/}
                          {/*delay={this.state.delay}*/}
                          {/*onError={this.handleError}*/}
                          {/*onScan={this.handleScan}*/}
                          {/*style={{width: '100%', margin: 'auto'}}*/}
                      {/*/>*/}
                  </div>

                  <ErrorMessage>
                        {error_message}
                  </ErrorMessage>

               </WrapperDiv>
          )
     } else if (this.props.loggedIn) {
          return (
              <WrapperDiv>
                  <h2>ENTER PURCHASE AMOUNT</h2>

                  <div>
                      <Input type="number"
                             onChange={this.handleChange}
                             placeholder="Enter Amount"
                             value={this.state.transfer_amount}
                      />
                      <StyledButton onClick={() => this.onAmountClick()}>Next</StyledButton>
                  </div>

                  <ErrorMessage>
                        {error_message}
                  </ErrorMessage>

              </WrapperDiv>
          )
     } else {
          return (
              <WrapperDiv>
                  <h2>VENDOR LOGIN</h2>

                  <VendorAuth/>

              </WrapperDiv>
          );
     }
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(deprecatedVendorPage);

const WrapperDiv = styled.div`
  //width: 100vw;
  //min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;