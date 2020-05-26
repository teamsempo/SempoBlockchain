import * as React from "react";
import { Mobile, Default } from "../helpers/responsive";
import { connect } from "react-redux";
import styled from "styled-components";
import { NavLink } from "react-router-dom";

import { ReduxState } from "../../reducers/rootReducer";
import { replaceSpaces } from "../../utils";
import MobileTopBar from "./MobileTopBar";
import OrgSwitcher from "./OrgSwitcher";
import { Organisation } from "../../reducers/organisation/types";
import { LoginState } from "../../reducers/auth/loginReducer";

interface StateProps {
  loggedIn: boolean;
  login: LoginState | null;
  email: string | null;
  activeOrganisation: Organisation;
  organisationList: Organisation[];
}

interface DispatchProps {}

const initialState = Object.freeze({
  iconURL: "/static/media/sempo_icon.svg",
  mobileMenuOpen: false,
  isOrgSwitcherActive: false
});

type Props = DispatchProps & StateProps;
type State = typeof initialState;

declare global {
  interface Window {
    DEPLOYMENT_NAME: string;
    ETH_EXPLORER_URL: string;
    USING_EXTERNAL_ERC20: boolean;
    master_wallet_address: string;
    ETH_CONTRACT_ADDRESS: string;
  }
}

class NavBar extends React.Component<Props, State> {
  readonly state = initialState;

  componentDidMount() {
    let activeOrg = this.props.activeOrganisation;
    let orgName =
      (activeOrg && replaceSpaces(activeOrg.name).toLowerCase()) || null;
    let deploymentName = window.DEPLOYMENT_NAME;

    //TODO: Allow setting of region for this
    let s3_region = "https://sempo-logos.s3-ap-southeast-2.amazonaws.com";
    let custom_url = `${s3_region}/${orgName}.${
      deploymentName === "dev" ? "svg" : "png"
    }`;

    console.log("Custom URL is", custom_url);

    this.imageExists(custom_url, exists => {
      if (exists) {
        this.setState({
          iconURL: custom_url
        });
      }
    });
  }

  componentWillUnmount() {
    this.setState({ mobileMenuOpen: false });
  }

  openMobileMenu = () => {
    this.setState(prevState => ({
      mobileMenuOpen: !prevState.mobileMenuOpen
    }));
  };

  imageExists(url: string, callback: (exists: boolean) => any) {
    var img = new Image();
    img.onload = function() {
      callback(true);
    };
    img.onerror = function() {
      callback(false);
    };
    img.src = url;
  }

  closeMobileMenu = () => this.setState({ mobileMenuOpen: false });

  render() {
    var tracker_link =
      window.ETH_EXPLORER_URL +
      "/address/" +
      (window.USING_EXTERNAL_ERC20
        ? window.master_wallet_address
        : window.ETH_CONTRACT_ADDRESS);

    let { loggedIn, email } = this.props;
    let { iconURL, mobileMenuOpen } = this.state;

    if (loggedIn) {
      return (
        <div>
          <SideBarWrapper mobileMenuOpen={mobileMenuOpen}>
            <Mobile>
              <MobileTopBar
                iconUrl={iconURL}
                email={email}
                menuOpen={mobileMenuOpen}
                onPress={this.openMobileMenu}
              />
            </Mobile>

            <SideBarNavigationItems>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <Default>
                  <OrgSwitcher
                    icon={iconURL}
                    selfPress={this.closeMobileMenu}
                  ></OrgSwitcher>
                </Default>

                <NavWrapper mobileMenuOpen={mobileMenuOpen}>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <StyledLink to="/" exact onClick={this.closeMobileMenu}>
                      Dashboard
                    </StyledLink>
                    <StyledLink to="/accounts" onClick={this.closeMobileMenu}>
                      Accounts
                    </StyledLink>
                    <StyledLink to="/transfers" onClick={this.closeMobileMenu}>
                      Transfers
                    </StyledLink>
                    <StyledLink to="/settings" onClick={this.closeMobileMenu}>
                      Settings
                    </StyledLink>
                  </div>
                  <ContractAddress href={tracker_link} target="_blank">
                    {window.USING_EXTERNAL_ERC20
                      ? "Master Wallet Tracker"
                      : "Contract Tracker"}
                  </ContractAddress>
                </NavWrapper>
              </div>
            </SideBarNavigationItems>
          </SideBarWrapper>
        </div>
      );
    } else {
      return <div></div>;
    }
  }
}

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    loggedIn: state.login.token != null,
    login: state.login,
    email: state.login.email,
    activeOrganisation:
      state.organisations.byId[Number(state.login.organisationId)],
    organisationList: Object.keys(state.organisations.byId).map(
      id => state.organisations.byId[Number(id)]
    )
  };
};

export default connect(mapStateToProps)(NavBar);

const SideBarWrapper = styled.div<any>`
  width: 234px;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background-color: #2b333b;
  -webkit-user-select: none;
  z-index: 501;
  @media (max-width: 767px) {
    display: flex;
    width: 100vw;
    flex-direction: column;
    height: ${props => (props.mobileMenuOpen ? "" : "50px")};
  }
`;

const NavWrapper = styled.div<any>`
  @media (max-width: 767px) {
    display: ${props => (props.mobileMenuOpen ? "" : "none")};
  }
`;

const SideBarNavigationItems = styled.div`
  display: flex;
  flex-direction: column;
`;

const activeClassName = "active-link";

const StyledLink = styled(NavLink).attrs({
  activeClassName
})`
  color: #9a9a9a;
  font-size: 12px;
  text-decoration: none;
  font-weight: 400;
  padding: 1em 2em;
  &:hover,
  &.${activeClassName} {
    color: #fff;
    background-color: #3d454d;
  }
  @media (max-width: 767px) {
    font-size: 16px;
  }
`;

const ContractAddress = styled.a`
  color: #fff;
  margin: auto 2em;
  font-size: 12px;
  text-decoration: none;
  font-weight: 400;
  position: absolute;
  bottom: 1em;
  @media (max-width: 767px) {
    text-align: center;
    font-size: 16px;
    left: 0;
    right: 0;
    color: #85898c;
  }
`;
