import React from 'react';
import styled from 'styled-components';
import {Redirect, Route, Switch, Link} from "react-router-dom";
import { connect } from 'react-redux';

import {activateAccount, logout} from '../../reducers/authReducer'

import LoginForm from '../auth/loginForm.jsx'
import RegisterForm from '../auth/registerForm.jsx'
import RequestResetEmailForm from '../auth/requestResetEmailForm.jsx'
import OrganisationForm from "../auth/OrganisationForm.jsx";


const mapStateToProps = (state) => {
  return {
    loggedIn: (state.login.userId !== null),
    loginState: state.login
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    activateAccount: (activation_token) => dispatch(activateAccount(activation_token))
  };
};

export class authPage extends React.Component {
  constructor() {
    super();
    this.state = {
      redirectToReferrer: false,
      email: null,
      organisation: null,
    };
  }

  componentDidMount() {
    // i.e. true if oxfam.sempo.ai else redirect to organisation form
    window.location.host.split('.') > 2 ? this.setState({organisation: window.location.host[0]}) : this.setState({organisation: null}, () => this.props.history.push('/login/organisation/'));

    const parsed = this.parseQuery(location.search);

    if (parsed.actok) {
      console.log('actok', parsed.actok)
      this.props.activateAccount(parsed.actok)
    }

    if (parsed.r && parsed.u) {
      this.setState({
        login: (!parsed.r === 'true'),
        email: parsed.u
      })
    }
  }

  componentDidUpdate(prevProps) {
    if (this.props.loggedIn !== prevProps.loggedIn) {
      this.setState({redirectToReferrer: true})
    }
  }

  parseQuery(queryString) {
    var query = {};
    var pairs = (queryString[0] === '?' ? queryString.substr(1) : queryString).split('&');
    for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i].split('=');
        query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
    }
    return query;
  }

  setOrganisation(org) {
    this.setState({organisation: org}, () => this.props.history.push('/login/'))
  }

  render() {
    let deploymentName = window.DEPLOYMENT_NAME;
      const { from } = this.props.location.state || { from: { pathname: "/" } };

      if (this.state.redirectToReferrer) {
          return <Redirect to={from} />;
      }

      return (
          <WrapperDiv>
              <LoginModuleBox>
                  <div>
                  <SempoLogoSVG src="/static/media/sempo_logo.svg"/>
                </div>
                <Switch>
                  <Route path={this.props.match.url + '/organisation/'} component={() => <OrganisationForm setOrganisationURL={(organisation) => this.setOrganisation(organisation)}/>} />
                  <Route path={this.props.match.url + '/forgot/'} component={forgotPassword} />
                  <Route path={this.props.match.url + '/sign-up/'} render={()=><Signup email={this.state.email} organisation={this.state.organisation}/>} />
                  <Route render={() => <LoginForm organisation={this.state.organisation}/>} />
                </Switch>
              </LoginModuleBox>
              <DeploymentNameText>sempo | {deploymentName}</DeploymentNameText>
              <TermsWrapper>
                <TermsText href='https://sempo.ai/legal/privacy/'>Privacy Policy</TermsText>
                <TermsText href='https://drive.google.com/file/d/1zv3LbBmpnwmCXrn310TO9X-OoGXL1ehu/view?usp=sharing'>Terms of Service</TermsText>
              </TermsWrapper>
          </WrapperDiv>
      )
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(authPage);


const forgotPassword = () => (
  <div>
    <div style={{position: 'relative'}}>
      <RequestResetEmailForm/>
    </div>
    <Footer>
        <FooterText>
          <FooterLink to="/login">Back to Login</FooterLink>
        </FooterText>
    </Footer>
  </div>
)

const Signup = ({email, organisation}) => (
  <div>
   <div className="form" style={{position: 'relative'}}>
    <RegisterForm email={email} organisation={organisation}/>
   </div>
    <Footer>
      <FooterText>
        Already have a Sempo account?
        <FooterLink to="/login">Login</FooterLink>
      </FooterText>
    </Footer>
  </div>
)

const TermsText = styled.a`
  margin: 10px;
  color: rgb(121, 127, 134);
  text-decoration: none;
`;

const TermsWrapper = styled.div`
  z-index: 999;
  bottom: 0px;
  color: rgb(121, 127, 134);
  font-size: 14px;
  position: absolute;
  text-align: center;
  padding: 10px 0px;
  display: flex;
`;

const WrapperDiv = styled.div`
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const SempoLogoSVG = styled.img`
  width: 200px;
  margin: auto;
  display: flex;
`;

export const Footer = styled.div`
  margin-top: 25px;
  font-size: 14px;
`;

export const FooterText = styled.p`
  margin: 0.5em;
  text-align: center;
`;

export const FooterLink = styled(Link)`
  color: #30a4a6;
  font-weight: bolder;
  text-decoration: none;
  margin-left: 0.5em;
  &:hover {
  text-decoration: underline;
  }
`;

const DeploymentNameText = styled.p`
  font-weight: 400;
  color: #9E9E9E;
  margin: 0;
`;

const LoginModuleBox = styled.div`
  width: calc(100vw - 80px);
  max-width: 350px;
  padding: 40px;
  margin: 1em 0;
  background-color: #fff;
  box-shadow: 0px 2px 0px 0 rgba(51,51,79,.08);
  overflow: hidden;
  position: relative;
  @media (max-width: 480px) {
    width: calc(100vw - 40px);
    padding: 40px 20px;
  }
`;