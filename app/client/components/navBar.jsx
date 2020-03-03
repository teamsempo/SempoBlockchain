import React from "react";
import MediaQuery from "react-responsive";
import { connect } from "react-redux";
import styled from "styled-components";
import { Link, NavLink } from "react-router-dom";

import { updateActiveOrgRequest } from "../reducers/auth/actions";
import { replaceSpaces } from "../utils";

const mapStateToProps = state => {
  return {
    loggedIn: state.login.token != null,
    login: state.login,
    email: state.login.email,
    activeOrganisation: state.organisations.byId[state.login.organisationId],
    organisationList: Object.keys(state.organisations.byId).map(
      id => state.organisations.byId[id]
    )
  };
};

const mapDispatchToProps = dispatch => {
  return {
    updateActiveOrgRequest: organisationId =>
      dispatch(
        updateActiveOrgRequest({
          organisationId
        })
      )
  };
};

class NavBar extends React.Component {
  constructor() {
    super();
    this.state = {
      iconURL: "/static/media/sempo_icon.svg",
      mobileMenuOpen: false,
      isOrgSwitcherActive: false
    };
  }

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

  handleClick() {
    this.setState({ mobileMenuOpen: false });
  }

  openMobileMenu() {
    this.setState(prevState => ({
      mobileMenuOpen: !prevState.mobileMenuOpen
    }));
  }

  selectOrg(org) {
    this.setState({ isOrgSwitcherActive: false }, () =>
      this.props.updateActiveOrgRequest(org.id)
    );
  }

  toggleSwitchOrgDropdown() {
    if (this.props.organisationList.length <= 1) {
      return;
    }

    this.setState(prevState => ({
      isOrgSwitcherActive: !prevState.isOrgSwitcherActive
    }));
  }

  imageExists(url, callback) {
    var img = new Image();
    img.onload = function() {
      callback(true);
    };
    img.onerror = function() {
      callback(false);
    };
    img.src = url;
  }

  _closeMobileMenu() {
    this.setState({ mobileMenuOpen: false });
  }

  render() {
    let deploymentName = window.DEPLOYMENT_NAME;
    let beneficiaryTermPlural = window.BENEFICIARY_TERM_PLURAL;
    let beneficiaryURL = "/" + beneficiaryTermPlural.toLowerCase();

    var tracker_link =
      window.ETH_EXPLORER_URL +
      "/address/" +
      (window.USING_EXTERNAL_ERC20
        ? window.master_wallet_address
        : window.ETH_CONTRACT_ADDRESS);

    var orgs = this.props.organisationList;
    if (orgs === null || typeof orgs === "undefined") {
      orgs = [];
    }

    if (this.props.loggedIn) {
      return (
        <div>
          <SideBarWrapper mobileMenuOpen={this.state.mobileMenuOpen}>
            <MediaQuery maxWidth={767}>
              <MobileTopBar>
                <StyledLogoLink to="/">
                  <SVG src={this.state.iconURL} />
                </StyledLogoLink>
                <Title>{this.props.email}</Title>
                <p
                  style={{ margin: "auto 1em", color: "#FFF" }}
                  onClick={() => this.openMobileMenu()}
                >
                  {this.state.mobileMenuOpen ? (
                    <SVG src="/static/media/close.svg" />
                  ) : (
                    <SVG src="/static/media/stack.svg" />
                  )}
                </p>
              </MobileTopBar>
            </MediaQuery>

            <SideBarNavigationItems>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <MediaQuery minWidth={768}>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "row",
                      cursor: "pointer"
                    }}
                  >
                    <StyledLogoLink
                      to="/"
                      onClick={() => this._closeMobileMenu()}
                    >
                      <SVG src={this.state.iconURL} />
                    </StyledLogoLink>
                    <div
                      style={{
                        display: "flex",
                        width: "100%",
                        justifyContent: "space-between"
                      }}
                      onClick={() => this.toggleSwitchOrgDropdown()}
                    >
                      <div style={{ margin: "auto 0", maxWidth: "100px" }}>
                        <BoldedNavBarHeaderText>
                          {this.props.activeOrganisation.name}
                        </BoldedNavBarHeaderText>
                        <StandardNavBarHeaderText>
                          {this.props.email}
                        </StandardNavBarHeaderText>
                      </div>
                      {orgs.length <= 1 ? null : (
                        <SVG
                          style={{ padding: "0 0.5em 0 0", width: "30px" }}
                          src={"/static/media/angle-down.svg"}
                        />
                      )}
                    </div>
                  </div>
                  <DropdownContent
                    style={{
                      display: this.state.isOrgSwitcherActive
                        ? "block"
                        : "none",
                      zIndex: 99
                    }}
                  >
                    <DropdownContentTitle>
                      Switch Organisation
                    </DropdownContentTitle>
                    {orgs.map(org => {
                      return (
                        <DropdownContentText
                          key={org.id}
                          onClick={() => this.selectOrg(org)}
                        >
                          {org.name}
                        </DropdownContentText>
                      );
                    })}
                  </DropdownContent>
                  <div
                    style={{
                      display: this.state.isOrgSwitcherActive
                        ? "block"
                        : "none",
                      position: "absolute",
                      top: 0,
                      left: 0,
                      zIndex: 98,
                      width: "100vw",
                      height: "100vh"
                    }}
                    onClick={() => this.toggleSwitchOrgDropdown()}
                  />
                </MediaQuery>

                <NavWrapper mobileMenuOpen={this.state.mobileMenuOpen}>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <StyledLink
                      to="/"
                      exact
                      onClick={() => this._closeMobileMenu()}
                    >
                      Dashboard
                    </StyledLink>
                    <StyledLink
                      to="/accounts"
                      onClick={() => this._closeMobileMenu()}
                    >
                      Accounts
                    </StyledLink>
                    <StyledLink
                      to="/transfers"
                      onClick={() => this._closeMobileMenu()}
                    >
                      Transfers
                    </StyledLink>
                    <StyledLink
                      to="/settings"
                      onClick={() => this._closeMobileMenu()}
                    >
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
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(NavBar);

const SideBarWrapper = styled.div`
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

const NavWrapper = styled.div`
  @media (max-width: 767px) {
    display: ${props => (props.mobileMenuOpen ? "" : "none")};
  }
`;

const Title = styled.h2`
  color: #fff;
  margin: auto 1em;
  font-size: 22px;
  font-weight: 600;
  text-decoration: none;
  letter-spacing: 1.5px;
  @media (max-width: 767px) {
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 16px;
    line-height: 1;
    text-align: center;
  }
`;

const SideBarNavigationItems = styled.div`
  display: flex;
  flex-direction: column;
`;

const SVG = styled.img`
  width: 35px;
  padding: 1em 0;
  display: flex;
  @media (max-width: 767px) {
    padding: 0;
    width: 30px;
  }
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

const MobileTopBar = styled.div`
  width: inherit;
  display: flex;
  justify-content: space-between;
  height: 50px;
`;

const StyledLogoLink = styled(NavLink)`
  color: #fff;
  margin: auto 1em;
  font-size: 22px;
  font-weight: 600;
  text-decoration: none;
  letter-spacing: 1.5px;
  @media (max-width: 767px) {
    margin: auto 0.5em;
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

const StandardNavBarHeaderText = styled.p`
  color: #fff;
  margin: 0;
  font-size: 12px;
  text-decoration: none;
  text-overflow: ellipsis;
  overflow: auto;
  overflow-x: hidden;
`;

const BoldedNavBarHeaderText = styled(StandardNavBarHeaderText)`
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
`;

const DropdownContent = styled.div`
  display: none;
  position: absolute;
  top: 74px;
  background-color: #f9f9f9;
  min-width: 160px;
  width: 234px;
  box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
  z-index: 1;
`;

const DropdownContentText = styled.p`
  color: black;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
  margin: 0;
  border-bottom: 0.5px solid #80808059;
  &:hover {
    background-color: #f1f1f1;
  }
`;

const DropdownContentTitle = styled(DropdownContentText)`
  text-transform: uppercase;
  font-size: 12px;
  font-weight: bold;
  color: grey;
  padding: 5px 16px;
`;
