import React from "react";
import styled from "styled-components";
import { Redirect, Route, Switch, Link } from "react-router-dom";
import { connect } from "react-redux";

import { ActivateAccountAction } from "../../reducers/auth/actions";

import LoginForm from "../auth/loginForm.jsx";
import RegisterForm from "../auth/registerForm.jsx";
import RequestResetEmailForm from "../auth/requestResetEmailForm.jsx";

import { parseQuery } from "../../utils";

const mapStateToProps = state => {
  return {
    loggedIn: state.login.userId !== null,
    loginState: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    activateAccount: payload =>
      dispatch(ActivateAccountAction.activateAccountRequest(payload))
  };
};

export class authPage extends React.Component {
  constructor() {
    super();
    this.state = {
      redirectToReferrer: false,
      email: null,
      referralCode: null
    };
  }

  componentDidMount() {
    const parsed = parseQuery(location.search);

    if (parsed.actok) {
      this.props.activateAccount({ body: { activation_token: parsed.actok } });
    }

    if (parsed.r && parsed.u) {
      this.setState({
        login: !parsed.r === "true",
        email: parsed.u,
        referralCode: parsed.c
      });
    }
  }

  componentDidUpdate() {
    if (this.props.loggedIn) {
      this.setState({ redirectToReferrer: true });
    }
  }

  render() {
    let deploymentName = window.DEPLOYMENT_NAME;
    const { from } = this.props.location.state || { from: { pathname: "/" } };

    if (this.state.redirectToReferrer || this.props.loggedIn) {
      return <Redirect to={from} />;
    }

    return (
      <WrapperDiv>
        <LoginModuleBox>
          <div style={{ paddingBottom: "24px" }}>
            <SempoLogoSVG
              src="/static/media/sempo_logo_teal.png"
              alt={"Sempo Logo"}
            />
          </div>
          <Switch>
            <Route
              path={this.props.match.url + "/forgot/"}
              component={forgotPassword}
            />
            <Route
              path={this.props.match.url + "/sign-up/"}
              render={() => (
                <Signup
                  email={this.state.email}
                  referralCode={this.state.referralCode}
                />
              )}
            />
            <Route component={LoginForm} />
          </Switch>
        </LoginModuleBox>
        <TermsText
          target="_blank"
          href={
            "https://docs.withsempo.com/sempo-dashboard/common-login-errors#what-to-do-if-you-encounter-issues-logging-in"
          }
        >
          Get help logging in
        </TermsText>
        <TermsWrapper>
          <TermsText href="#">· Sempo - {deploymentName}</TermsText>
          <TermsText href="https://withsempo.com/legal/privacy-policy/">
            · Privacy Policy
          </TermsText>
          <TermsText href="https://withsempo.com/legal/platform-terms/">
            · Terms of Service
          </TermsText>
        </TermsWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(authPage);

const forgotPassword = () => (
  <div>
    <div style={{ position: "relative" }}>
      <RequestResetEmailForm />
    </div>
    <Footer>
      <FooterText>
        <FooterLink to="/login">Back to Login</FooterLink>
      </FooterText>
    </Footer>
  </div>
);

const Signup = ({ email, referralCode }) => (
  <div>
    <div className="form" style={{ position: "relative" }}>
      <RegisterForm email={email} referralCode={referralCode} />
    </div>
    <Footer>
      <FooterText>
        Already have a Sempo account?
        <FooterLink to="/login">Login</FooterLink>
      </FooterText>
    </Footer>
  </div>
);

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

const LoginModuleBox = styled.div`
  width: calc(100vw - 80px);
  max-width: 350px;
  padding: 40px;
  margin: 1em 0;
  background-color: #fff;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  overflow: hidden;
  position: relative;
  @media (max-width: 480px) {
    width: calc(100vw - 40px);
    padding: 40px 20px;
  }
`;
