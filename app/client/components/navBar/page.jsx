import React from "react";
import { Layout, Menu, Typography } from "antd";
import { NavLink } from "react-router-dom";

import {
  DesktopOutlined,
  SendOutlined,
  TeamOutlined,
  SettingOutlined
} from "@ant-design/icons";

const { Header, Content, Footer, Sider } = Layout;
const { SubMenu } = Menu;
const { Title } = Typography;

export default class Page extends React.Component {
  state = {
    collapsed: false
  };

  onCollapse = collapsed => {
    console.log(collapsed);
    this.setState({ collapsed });
  };

  render() {
    return (
      <Layout style={{ minHeight: "100vh" }}>
        {this.props.noNav ? null : (
          <Sider
            collapsible
            collapsed={this.state.collapsed}
            onCollapse={this.onCollapse}
          >
            <div className="logo" />
            <Menu
              theme="dark"
              defaultSelectedKeys={[
                "/" + this.props.location.pathname.split("/")[1]
              ]}
              mode="inline"
            >
              <SubMenu
                key="sub1"
                icon={<DesktopOutlined translate={""} />}
                title="Dashboard"
              >
                <Menu.Item key="/">
                  <NavLink to="/">Analytics</NavLink>
                </Menu.Item>
                <Menu.Item key="/map">
                  <NavLink to="/map">Map</NavLink>
                </Menu.Item>
              </SubMenu>
              <Menu.Item key="/accounts" icon={<TeamOutlined translate={""} />}>
                <NavLink to="/accounts">Accounts</NavLink>
              </Menu.Item>
              <Menu.Item
                key="/transfers"
                icon={<SendOutlined translate={""} />}
              >
                <NavLink to="/transfers">Transfers</NavLink>
              </Menu.Item>
              <Menu.Item
                key="/settings"
                icon={<SettingOutlined translate={""} />}
              >
                <NavLink to="/settings">Settings</NavLink>
              </Menu.Item>
            </Menu>
          </Sider>
        )}

        <Layout className="site-layout">
          {this.props.title ? (
            <Header className="site-layout-background" style={{ padding: 0 }}>
              <Title>{this.props.title}</Title>
            </Header>
          ) : null}
          <Content style={{ margin: "0 16px" }}>{this.props.children}</Content>
          {this.props.footer ? (
            <Footer style={{ textAlign: "center" }}>Sempo ©2020</Footer>
          ) : null}
        </Layout>
      </Layout>
    );
  }
}

Page.defaultProps = {
  footer: true
};
