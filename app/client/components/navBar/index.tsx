import * as React from "react";
import { connect } from "react-redux";
import { NavLink } from "react-router-dom";
import { Layout, Menu } from "antd";
import { IntercomChat } from "../intercom/IntercomChat";
import { IntercomHelpCentre } from "../intercom/IntercomHelpCentre";

import {
  DesktopOutlined,
  SendOutlined,
  TeamOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  StockOutlined,
  CompassOutlined
} from "@ant-design/icons";

const { Sider } = Layout;
const { SubMenu } = Menu;

import { ReduxState } from "../../reducers/rootReducer";
import { replaceSpaces } from "../../utils";
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

interface ComponentProps {
  pathname: string;
}

const initialState = Object.freeze({
  iconURL: "/static/media/sempo_icon.svg",
  isOrgSwitcherActive: false,
  collapsed: false
});

type Props = DispatchProps & StateProps & ComponentProps;
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

  onCollapse = (collapsed: boolean) => {
    this.setState({ collapsed });
  };

  render() {
    var tracker_link =
      window.ETH_EXPLORER_URL +
      "/address/" +
      (window.USING_EXTERNAL_ERC20
        ? window.master_wallet_address
        : window.ETH_CONTRACT_ADDRESS);

    let { loggedIn, email, pathname } = this.props;
    let { iconURL, collapsed } = this.state;

    let activePath = pathname && "/" + pathname.split("/")[1];

    if (loggedIn) {
      return (
        <Sider collapsible collapsed={collapsed} onCollapse={this.onCollapse}>
          <OrgSwitcher icon={iconURL} collapsed={collapsed}></OrgSwitcher>
          <Menu theme="dark" selectedKeys={[activePath]} mode="vertical">
            <SubMenu
              key="sub1"
              icon={<DesktopOutlined translate={""} />}
              title="Dashboard"
            >
              <Menu.Item key="/">
                <NavLink to="/">
                  <StockOutlined translate={""} /> Analytics
                </NavLink>
              </Menu.Item>
              <Menu.Item key="/map">
                <NavLink to="/map">
                  <CompassOutlined translate={""} /> Map
                </NavLink>
              </Menu.Item>
            </SubMenu>
            <Menu.Item key="/accounts" icon={<TeamOutlined translate={""} />}>
              <NavLink to="/accounts">Accounts</NavLink>
            </Menu.Item>
            <Menu.Item key="/transfers" icon={<SendOutlined translate={""} />}>
              <NavLink to="/transfers">Transfers</NavLink>
            </Menu.Item>
            <Menu.Item
              key="/settings"
              icon={<SettingOutlined translate={""} />}
            >
              <NavLink to="/settings">Settings</NavLink>
            </Menu.Item>
          </Menu>

          <Menu
            theme="dark"
            mode="vertical"
            style={{
              position: "fixed",
              bottom: "60px",
              width: collapsed ? 80 : 200
            }}
            selectable={false}
          >
            <SubMenu
              key="help"
              icon={<QuestionCircleOutlined translate={""} />}
              title="Help"
            >
              <Menu.Item key="help-centre">
                <IntercomHelpCentre />
              </Menu.Item>
              <Menu.Item key="contact-support">
                <IntercomChat />
              </Menu.Item>
            </SubMenu>
          </Menu>
        </Sider>
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
