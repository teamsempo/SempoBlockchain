import * as React from "react";
import { connect } from "react-redux";
import { NavLink } from "react-router-dom";
import { Layout, Menu } from "antd";
import { IntercomChat } from "../intercom/IntercomChat";
import { HelpCentre } from "../intercom/HelpCentre";

import {
  DesktopOutlined,
  SendOutlined,
  TeamOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  StockOutlined,
  CompassOutlined,
  UnorderedListOutlined,
  DollarOutlined
} from "@ant-design/icons";

const { Sider } = Layout;
const { SubMenu } = Menu;

import { ReduxState } from "../../reducers/rootReducer";
import { replaceSpaces } from "../../utils";
import OrgSwitcher from "./OrgSwitcher";
import { Organisation } from "../../reducers/organisation/types";
import { LoginState } from "../../reducers/auth/loginReducer";
import { isMobileQuery, withMediaQuery } from "../helpers/responsive";

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
  isMobile: boolean;
  onCollapse: (collapsed: boolean) => any;
  collapsed: boolean;
}

const initialState = Object.freeze({
  iconURL: "/static/media/sempo_icon.svg",
  isOrgSwitcherActive: false
});

type Props = DispatchProps & StateProps & ComponentProps;
type State = typeof initialState;

declare global {
  interface Window {
    DEPLOYMENT_NAME: string;
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
    let custom_url = `${s3_region}/${orgName}.png`;

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

  render() {
    let { loggedIn, pathname, isMobile, collapsed } = this.props;
    let { iconURL } = this.state;

    let activePath = pathname && "/" + pathname.split("/")[1];

    if (loggedIn) {
      return (
        <Sider
          collapsible={!isMobile}
          collapsed={collapsed}
          onCollapse={collapsed => this.props.onCollapse(collapsed)}
          breakpoint={isMobile ? "md" : undefined}
          collapsedWidth={isMobile ? "0" : undefined}
          style={{ position: "fixed", zIndex: 99, height: "100%" }}
        >
          <OrgSwitcher icon={iconURL} collapsed={collapsed}></OrgSwitcher>
          <Menu
            theme="dark"
            selectedKeys={[activePath]}
            mode={isMobile ? "inline" : "vertical"}
          >
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

            <SubMenu
              key="sub2"
              icon={<DollarOutlined translate={""} />}
              title="Transfers"
            >
              <Menu.Item
                key="/transfers"
                icon={<UnorderedListOutlined translate={""} />}
              >
                <NavLink to="/transfers">Transfers List</NavLink>
              </Menu.Item>
              <Menu.Item key="/bulk" icon={<SendOutlined translate={""} />}>
                <NavLink to="/bulk/create">Bulk Disbursement</NavLink>
              </Menu.Item>
            </SubMenu>

            <Menu.Item
              key="/settings"
              icon={<SettingOutlined translate={""} />}
            >
              <NavLink to="/settings">Settings</NavLink>
            </Menu.Item>
          </Menu>

          <Menu
            theme="dark"
            mode={isMobile ? "inline" : "vertical"}
            style={
              isMobile
                ? undefined
                : {
                    position: "fixed",
                    bottom: "60px",
                    width: collapsed ? 80 : 200
                  }
            }
            selectable={false}
          >
            <SubMenu
              key="help"
              icon={<QuestionCircleOutlined translate={""} />}
              title="Help"
            >
              <Menu.Item key="help-centre">
                <HelpCentre />
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

export default connect(mapStateToProps)(
  withMediaQuery([isMobileQuery])(NavBar)
);
