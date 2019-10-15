import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { Input, StyledButton, ErrorMessage } from '../styledElements'

import { loginRequest } from '../../reducers/authReducer'

const mapStateToProps = (state) => {
  return {
    login_status: state.login,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loginRequest: (payload) => dispatch(loginRequest(payload)),
  };
};

class vendorAuth extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
        vendor_missing: false,
        invalid_login: false,
        vendor_code: '',
    };
    this.handleChange = this.handleChange.bind(this);
  }

  componentWillReceiveProps(nextProps) {
    this.setState({invalid_login: (nextProps.login_status.error)})
  }

  handleChange(event) {
      this.setState({vendor_code: event.target.value});
  }

  attemptLogin() {
    if (this.state.vendor_code.length < 6) {
      this.setState({vendor_missing: true});
      return
    }
    console.log('here');
    console.log(this.state.vendor_code);
    this.setState({vendor_missing: false});
    this.props.loginRequest({body:{username: this.state.vendor_code}})
  }

  onClick(){
    this.attemptLogin()
  }

  render() {

      if (this.state.vendor_missing) {
        var error_message = 'Enter a 6 digit code'
      } else if (this.state.invalid_login) {
        error_message = 'Incorrect Vendor Code'
      } else {
        error_message = ''
      }

          return(
                    <div>

                      <Input type="text"
                             id="VenderField"
                             onChange={this.handleChange}
                             placeholder="6 Digit Code"
                             maxLength={6}
                             value={this.state.vendor_code}
                      />

                      <ErrorMessage>
                        {error_message}
                      </ErrorMessage>

                      <StyledButton onClick={() => this.onClick()}> Login </StyledButton>
                    </div>
          );
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(vendorAuth);

const WrapperDiv = styled.div`
  //width: 100vw;
  //min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;