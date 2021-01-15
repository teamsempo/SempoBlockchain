import React from "react";
import styled from "styled-components";
import QRCode from "qrcode.react";

import AsyncButton from "./../AsyncButton.jsx";
import TFAValidator from "./TFAValidator.jsx";

import { FooterLink } from "../pages/authPage.jsx";

export default class TFAForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      showQR: props.tfaURL ? true : false
    };
  }

  handleNextBack() {
    this.setState({
      showQR: !this.state.showQR
    });
  }

  render() {
    if (this.state.showQR) {
      return (
        <div>
          <TFAQr data={this.props.tfaURL} />
          <AsyncButton
            onClick={() => this.handleNextBack()}
            buttonStyle={{ width: "calc(100% - 1em)", display: "flex" }}
            buttonText={<span>Next</span>}
            label={
              "Go to the next page once two factor authentication QR code is scanned"
            }
          />
        </div>
      );
    } else {
      return (
        <div>
          <TFAValidator />
          {this.props.tfaURL ? (
            <div onClick={() => this.handleNextBack()}>
              <FooterLink to={"#"}>Back</FooterLink>
            </div>
          ) : (
            <div></div>
          )}
        </div>
      );
    }
  }
}

const TFAQr = props => (
  <TFAQRContainer>
    <div>
      <QRCode value={props.data} />
    </div>
    <div>
      <div style={{ margin: "0.5em" }}>
        Scan the code above using an app like Google Authenticator.
      </div>
      <div>
        (
        <ExternalLink
          href="https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2"
          target="_blank"
          label={"Google Play Store Two Factor Authentication Application"}
        >
          Android
        </ExternalLink>
        /
        <ExternalLink
          href="https://apps.apple.com/au/app/google-authenticator/id388497605"
          target="_blank"
          label={"Apple App Store Two Factor Authentication Application"}
        >
          iPhone
        </ExternalLink>
        )
      </div>
    </div>
  </TFAQRContainer>
);

const TFAQRContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 1em;
  text-align: center;
`;

export const ExternalLink = styled.a`
  color: #30a4a6;
  font-weight: bolder;
  text-decoration: none;
  margin-left: 0em;
  &:hover {
    text-decoration: underline;
  }
`;
